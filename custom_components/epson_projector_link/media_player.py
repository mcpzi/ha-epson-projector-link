"""Support for Epson projector."""

import logging

from homeassistant.components.media_player import MediaPlayerDeviceClass
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import MediaPlayerEntityFeature
from homeassistant.helpers import entity_platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import voluptuous as vol

from . import EpsonProjectorLinkConfigEntry
from .const import DOMAIN
from .const import SERVICE_ERASE_PICTURE_MEMORY
from .const import SERVICE_LOAD_LENS_MEMORY
from .const import SERVICE_LOAD_PICTURE_MEMORY
from .const import SERVICE_PUSH_PICTURE_MEMORY
from .const import SERVICE_SEND_COMMAND
from .const import STATE_ERROR
from .projector.const import COMMAND_ERASE_PICTURE_MEMORY
from .projector.const import COMMAND_LOAD_LENS_MEMORY
from .projector.const import COMMAND_LOAD_PICTURE_MEMORY
from .projector.const import COMMAND_MEDIA_NEXT
from .projector.const import COMMAND_MEDIA_PAUSE
from .projector.const import COMMAND_MEDIA_PLAY
from .projector.const import COMMAND_MEDIA_PREVIOUS
from .projector.const import COMMAND_MEDIA_STOP
from .projector.const import COMMAND_MEDIA_VOL_DOWN
from .projector.const import COMMAND_MEDIA_VOL_UP
from .projector.const import COMMAND_PUSH_PICTURE_MEMORY
from .projector.const import ERROR_NONE
from .projector.const import OFF
from .projector.const import ON
from .projector.const import PROPERTY_ERR
from .projector.const import PROPERTY_MUTE
from .projector.const import PROPERTY_POWER
from .projector.const import PROPERTY_SOURCE
from .projector.const import PROPERTY_SOURCE_LIST
from .projector.const import PROPERTY_VOLUME
from .projector.const import SOURCE_CODE_INVERTED_MAP
from .projector.const import STATE_COOLDOWN
from .projector.const import STATE_WARMUP

_LOGGER = logging.getLogger(__name__)

PROPERTY_TO_FEATURE_MAP = {
    PROPERTY_SOURCE: MediaPlayerEntityFeature.SELECT_SOURCE,
    PROPERTY_VOLUME: MediaPlayerEntityFeature.VOLUME_SET,
    PROPERTY_MUTE: MediaPlayerEntityFeature.VOLUME_MUTE,
}


async def async_setup_entry(
    hass, config_entry: EpsonProjectorLinkConfigEntry, async_add_entities
):
    """Set up the Epson projector media player from a config entry."""
    _LOGGER.debug("async_setup_entry: entry_id=%s", config_entry.entry_id)
    data = config_entry.runtime_data
    async_add_entities(
        [
            EpsonProjectorMediaPlayer(
                config_entry=config_entry,
                projector=data.projector,
                power_coordinator=data.power_coordinator,
                properties_coordinator=data.properties_coordinator,
                poll_properties=data.poll_properties,
            )
        ]
    )

    _setup_services()


def _setup_services():
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_LOAD_LENS_MEMORY,
        {
            vol.Required("lens_memory_id"): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=10)
            )
        },
        SERVICE_LOAD_LENS_MEMORY,
    )
    platform.async_register_entity_service(
        SERVICE_LOAD_PICTURE_MEMORY,
        {
            vol.Required("picture_memory_id"): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=10)
            )
        },
        SERVICE_LOAD_PICTURE_MEMORY,
    )
    platform.async_register_entity_service(
        SERVICE_PUSH_PICTURE_MEMORY,
        {
            vol.Required("picture_memory_id"): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=10)
            )
        },
        SERVICE_PUSH_PICTURE_MEMORY,
    )
    platform.async_register_entity_service(
        SERVICE_ERASE_PICTURE_MEMORY,
        {
            vol.Required("picture_memory_id"): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=10)
            )
        },
        SERVICE_ERASE_PICTURE_MEMORY,
    )
    platform.async_register_entity_service(
        SERVICE_SEND_COMMAND,
        {vol.Required("command"): str},
        SERVICE_SEND_COMMAND,
    )


def _get_supported_features(properties):
    features = MediaPlayerEntityFeature.TURN_OFF | MediaPlayerEntityFeature.TURN_ON

    for prop in properties:
        additional_features = PROPERTY_TO_FEATURE_MAP.get(prop)
        if additional_features is not None:
            features |= additional_features

    return features


def _to_hex(integer):
    return "%0.2X" % integer


class EpsonProjectorMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of Epson Projector Home Cinema Device."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_translation_key = "projector"

    def __init__(
        self,
        config_entry,
        projector,
        power_coordinator,
        properties_coordinator,
        poll_properties,
    ):
        """Initialize projector entity."""
        # Keep using the power coordinator as the primary coordinator so entity
        # availability tracks the projector's reachability.
        super().__init__(power_coordinator)
        self._config_entry = config_entry
        self._projector = projector
        self._properties_coordinator = properties_coordinator
        self._attr_supported_features = _get_supported_features(poll_properties)
        # Unique ID intentionally has no suffix to preserve existing entity IDs
        # from before this entity was one of several under the same device.
        self._attr_unique_id = config_entry.unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.unique_id)}
        )

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._properties_coordinator.async_add_listener(
                self._handle_coordinator_update
            )
        )

    @property
    def state(self):
        """Return the state of the device."""
        power_state = self.coordinator.data
        error = self._properties_coordinator.data.get(PROPERTY_ERR)
        if (
            power_state in (STATE_WARMUP, STATE_COOLDOWN)
            and error is not None
            and error != ERROR_NONE
        ):
            return STATE_ERROR
        return power_state

    @property
    def source(self):
        """Return the current input source."""
        return self._properties_coordinator.data.get(PROPERTY_SOURCE)

    @property
    def source_list(self):
        """Return the list of available input sources."""
        return self._properties_coordinator.data.get(PROPERTY_SOURCE_LIST)

    @property
    def volume_level(self):
        """Return the volume level."""
        volume = self._properties_coordinator.data.get(PROPERTY_VOLUME)
        return None if volume is None else volume / 100

    @property
    def is_volume_muted(self):
        """Return whether volume is muted."""
        return self._properties_coordinator.data.get(PROPERTY_MUTE)

    async def async_turn_on(self):
        await self._projector.set_property(PROPERTY_POWER, ON)

    async def async_turn_off(self):
        await self._projector.set_property(PROPERTY_POWER, OFF)

    async def async_select_source(self, source):
        source_code = SOURCE_CODE_INVERTED_MAP.get(source, source)
        await self._projector.set_property(PROPERTY_SOURCE, source_code)

    async def async_set_volume_level(self, volume):
        await self._projector.set_property(PROPERTY_VOLUME, int(volume * 100))

    async def async_mute_volume(self, mute):
        await self._projector.set_property(PROPERTY_MUTE, ON if mute else OFF)

    async def async_volume_up(self):
        await self._projector.send_command(COMMAND_MEDIA_VOL_UP)

    async def async_volume_down(self):
        await self._projector.send_command(COMMAND_MEDIA_VOL_DOWN)

    async def async_media_pause(self):
        await self._projector.send_command(COMMAND_MEDIA_PAUSE)

    async def async_media_play(self):
        await self._projector.send_command(COMMAND_MEDIA_PLAY)

    async def async_media_stop(self):
        await self._projector.send_command(COMMAND_MEDIA_STOP)

    async def async_media_next_track(self):
        await self._projector.send_command(COMMAND_MEDIA_NEXT)

    async def async_media_previous_track(self):
        await self._projector.send_command(COMMAND_MEDIA_PREVIOUS)

    #
    # Custom Services
    #

    async def load_lens_memory(self, lens_memory_id):
        await self._projector.send_command(
            COMMAND_LOAD_LENS_MEMORY, _to_hex(lens_memory_id)
        )

    async def load_picture_memory(self, picture_memory_id):
        await self._projector.send_command(
            # 02 is for MEMORY Type
            COMMAND_LOAD_PICTURE_MEMORY,
            f"02 {_to_hex(picture_memory_id)}",
        )

    async def push_picture_memory(self, picture_memory_id):
        await self._projector.send_command(
            # 02 is for MEMORY Type
            COMMAND_PUSH_PICTURE_MEMORY,
            f"02 {_to_hex(picture_memory_id)}",
        )

    async def erase_picture_memory(self, picture_memory_id):
        await self._projector.send_command(
            # 02 is for MEMORY Type
            COMMAND_ERASE_PICTURE_MEMORY,
            f"02 {_to_hex(picture_memory_id)}",
        )

    async def send_command(self, command):
        await self._projector.send_command(command)
