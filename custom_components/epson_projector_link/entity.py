"""Base entity for Epson Projector Link entities."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class EpsonProjectorEntity(CoordinatorEntity):
    """Base class for Epson Projector Link entities tied to the projector device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, device_unique_id, key):
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{device_unique_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_unique_id)})
