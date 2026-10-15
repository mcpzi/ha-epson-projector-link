"""Support for Epson projector select entities."""

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory

from . import EpsonProjectorLinkConfigEntry
from .entity import EpsonProjectorEntity
from .projector.const import AUTO_IRIS_MODE_CODE_INVERTED_MAP
from .projector.const import AUTO_IRIS_MODE_CODE_MAP
from .projector.const import COLOR_MODE_CODE_INVERTED_MAP
from .projector.const import COLOR_MODE_CODE_MAP
from .projector.const import POWER_CONSUMPTION_MODE_CODE_INVERTED_MAP
from .projector.const import POWER_CONSUMPTION_MODE_CODE_MAP
from .projector.const import PROPERTY_AUTO_IRIS_MODE
from .projector.const import PROPERTY_COLOR_MODE
from .projector.const import PROPERTY_POWER_CONSUMPTION_MODE

SELECT_DESCRIPTIONS = [
    (PROPERTY_AUTO_IRIS_MODE, "auto_iris_mode", AUTO_IRIS_MODE_CODE_MAP, AUTO_IRIS_MODE_CODE_INVERTED_MAP),
    (PROPERTY_COLOR_MODE, "color_mode", COLOR_MODE_CODE_MAP, COLOR_MODE_CODE_INVERTED_MAP),
    (
        PROPERTY_POWER_CONSUMPTION_MODE,
        "power_consumption_mode",
        POWER_CONSUMPTION_MODE_CODE_MAP,
        POWER_CONSUMPTION_MODE_CODE_INVERTED_MAP,
    ),
]


async def async_setup_entry(
    hass, config_entry: EpsonProjectorLinkConfigEntry, async_add_entities
):
    """Set up Epson projector select entities from a config entry."""
    data = config_entry.runtime_data
    entities = [
        EpsonProjectorSelect(
            data.properties_coordinator,
            data.projector,
            config_entry.unique_id,
            key,
            prop,
            list(code_map.values()),
            option_to_code,
        )
        for prop, key, code_map, option_to_code in SELECT_DESCRIPTIONS
        if prop in data.poll_properties
    ]
    async_add_entities(entities)


class EpsonProjectorSelect(EpsonProjectorEntity, SelectEntity):
    """Select entity for an Epson projector mode property."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, projector, device_unique_id, key, prop, options, option_to_code):
        """Initialize the select entity."""
        super().__init__(coordinator, device_unique_id, key)
        self._projector = projector
        self._property = prop
        self._option_to_code = option_to_code
        self._attr_options = options

    @property
    def current_option(self):
        """Return the current mode."""
        return self.coordinator.data.get(self._property)

    async def async_select_option(self, option):
        """Set the mode."""
        await self._projector.set_property(
            self._property, self._option_to_code[option]
        )
