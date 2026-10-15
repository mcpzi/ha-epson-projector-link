"""The Epson Projector Link integration."""

from dataclasses import dataclass
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_POLL_PROPERTIES
from .const import CONF_PROPERTIES_SCAN_INTERVAL
from .const import DOMAIN
from .const import MANUFACTURER
from .const import MODEL
from .coordinator import EpsonProjectorPowerCoordinator
from .coordinator import EpsonProjectorPropertiesCoordinator
from .projector import Projector
from .projector.const import PROPERTY_ERR
from .projector.const import PROPERTY_POWER

PLATFORMS = [
    Platform.MEDIA_PLAYER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

_LOGGER = logging.getLogger(__name__)


@dataclass
class EpsonProjectorLinkData:
    """Runtime data for an Epson Projector Link config entry."""

    projector: Projector
    power_coordinator: EpsonProjectorPowerCoordinator
    properties_coordinator: EpsonProjectorPropertiesCoordinator
    poll_properties: list


type EpsonProjectorLinkConfigEntry = ConfigEntry[EpsonProjectorLinkData]


def create_projector(data):
    return Projector(
        host=data[CONF_HOST],
        password=data.get(CONF_PASSWORD) or None,
    )


def _to_time_delta_seconds(scan_interval):
    return (
        timedelta(seconds=scan_interval)
        if isinstance(scan_interval, int)
        else scan_interval
    )


async def async_setup_entry(
    hass: HomeAssistant, config_entry: EpsonProjectorLinkConfigEntry
) -> bool:
    """Set up epson from a config entry."""
    projector = create_projector(config_entry.data)
    poll_properties = config_entry.data[CONF_POLL_PROPERTIES]

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, config_entry.unique_id)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=config_entry.title,
    )

    power_coordinator = EpsonProjectorPowerCoordinator(
        hass,
        config_entry,
        projector,
        _to_time_delta_seconds(config_entry.data[CONF_SCAN_INTERVAL]),
    )
    properties_coordinator = EpsonProjectorPropertiesCoordinator(
        hass,
        config_entry,
        projector,
        power_coordinator,
        poll_properties,
        _to_time_delta_seconds(config_entry.data[CONF_PROPERTIES_SCAN_INTERVAL]),
    )

    def _on_projector_event(prop, value):
        # Only PWR and ERR are pushed unsolicited by the projector (e.g. IMEVENT).
        # Other properties are only ever returned as a response to our own
        # coordinator polling, which already captures their value directly.
        if prop == PROPERTY_POWER:
            power_coordinator.handle_push_update(value)
        elif prop == PROPERTY_ERR:
            properties_coordinator.handle_push_update(prop, value)

    projector.set_callback(_on_projector_event)

    config_entry.runtime_data = EpsonProjectorLinkData(
        projector=projector,
        power_coordinator=power_coordinator,
        properties_coordinator=properties_coordinator,
        poll_properties=poll_properties,
    )

    # Use async_refresh (not async_config_entry_first_refresh) so the entry still
    # loads with entities marked unavailable when the projector cannot be reached
    # yet (e.g. it is fully powered off with network standby disabled).
    await power_coordinator.async_refresh()

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    return True


async def update_listener(
    hass: HomeAssistant, config_entry: EpsonProjectorLinkConfigEntry
) -> None:
    """Update options."""
    if config_entry.data == config_entry.options:
        _LOGGER.debug(
            "update_listener: No changes in options for %s", config_entry.entry_id
        )
        return

    _LOGGER.debug(
        "update_listener: Updating options and reloading %s", config_entry.entry_id
    )
    hass.config_entries.async_update_entry(
        entry=config_entry,
        data=config_entry.options.copy(),
    )
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, config_entry: EpsonProjectorLinkConfigEntry
) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    if unloaded:
        data = config_entry.runtime_data
        await data.power_coordinator.async_shutdown()
        await data.properties_coordinator.async_shutdown()
        data.projector.close()
    return unloaded
