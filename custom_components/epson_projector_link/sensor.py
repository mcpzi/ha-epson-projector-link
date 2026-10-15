"""Support for Epson projector sensors."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from . import EpsonProjectorLinkConfigEntry
from .entity import EpsonProjectorEntity
from .projector.const import PROPERTY_ERR
from .projector.const import PROPERTY_FOCUS
from .projector.const import PROPERTY_LAMP_HOURS
from .projector.const import PROPERTY_LENS_SHIFT_HORIZONTAL
from .projector.const import PROPERTY_LENS_SHIFT_VERTICAL
from .projector.const import PROPERTY_ZOOM

# (property, key) pairs for simple read-only numeric sensors, gated on the
# property being enabled in "Additional properties to poll". These report
# the projector's raw internal position/step value; Epson does not document
# a min/max range for them, so they are read-only rather than number entities.
POSITION_SENSOR_DESCRIPTIONS = [
    (PROPERTY_LENS_SHIFT_HORIZONTAL, "lens_shift_horizontal"),
    (PROPERTY_LENS_SHIFT_VERTICAL, "lens_shift_vertical"),
    (PROPERTY_FOCUS, "focus"),
    (PROPERTY_ZOOM, "zoom"),
]


async def async_setup_entry(
    hass, config_entry: EpsonProjectorLinkConfigEntry, async_add_entities
):
    """Set up Epson projector sensors from a config entry."""
    data = config_entry.runtime_data
    entities = [
        EpsonProjectorErrorSensor(data.properties_coordinator, config_entry.unique_id)
    ]
    if PROPERTY_LAMP_HOURS in data.poll_properties:
        entities.append(
            EpsonProjectorLampHoursSensor(
                data.properties_coordinator, config_entry.unique_id
            )
        )
    entities.extend(
        EpsonProjectorPositionSensor(
            data.properties_coordinator, config_entry.unique_id, key, prop
        )
        for prop, key in POSITION_SENSOR_DESCRIPTIONS
        if prop in data.poll_properties
    )
    async_add_entities(entities)


class EpsonProjectorErrorSensor(EpsonProjectorEntity, SensorEntity):
    """Sensor for the current projector error, if any."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_unique_id):
        """Initialize the sensor."""
        super().__init__(coordinator, device_unique_id, "error")

    @property
    def native_value(self):
        """Return the current error."""
        return self.coordinator.data.get(PROPERTY_ERR)


class EpsonProjectorLampHoursSensor(EpsonProjectorEntity, SensorEntity):
    """Sensor for the projector lamp hours."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, device_unique_id):
        """Initialize the sensor."""
        super().__init__(coordinator, device_unique_id, "lamp_hours")

    @property
    def native_value(self):
        """Return the lamp hours."""
        return self.coordinator.data.get(PROPERTY_LAMP_HOURS)


class EpsonProjectorPositionSensor(EpsonProjectorEntity, SensorEntity):
    """Read-only sensor for a lens/picture position value (lens shift, focus, zoom).

    Epson's command guide does not document a min/max range for these, and
    the raw values are projector-internal step counts rather than a
    percentage, so they're exposed read-only instead of as number entities.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_unique_id, key, prop):
        """Initialize the sensor."""
        super().__init__(coordinator, device_unique_id, key)
        self._property = prop

    @property
    def native_value(self):
        """Return the current position value."""
        return self.coordinator.data.get(self._property)
