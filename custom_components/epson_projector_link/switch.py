"""Support for Epson projector power switch."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_ON

from . import EpsonProjectorLinkConfigEntry
from .entity import EpsonProjectorEntity
from .projector.const import OFF
from .projector.const import ON
from .projector.const import PROPERTY_POWER


async def async_setup_entry(
    hass, config_entry: EpsonProjectorLinkConfigEntry, async_add_entities
):
    """Set up the Epson projector power switch from a config entry."""
    data = config_entry.runtime_data
    async_add_entities(
        [
            EpsonProjectorPowerSwitch(
                data.power_coordinator, data.projector, config_entry.unique_id
            )
        ]
    )


class EpsonProjectorPowerSwitch(EpsonProjectorEntity, SwitchEntity):
    """Switch to power the projector on and off."""

    def __init__(self, coordinator, projector, device_unique_id):
        """Initialize the switch."""
        super().__init__(coordinator, device_unique_id, "power")
        self._projector = projector

    @property
    def is_on(self):
        """Return whether the projector is powered on."""
        return self.coordinator.data == STATE_ON

    async def async_turn_on(self, **kwargs):
        """Turn the projector on."""
        await self._projector.set_property(PROPERTY_POWER, ON)

    async def async_turn_off(self, **kwargs):
        """Turn the projector off."""
        await self._projector.set_property(PROPERTY_POWER, OFF)
