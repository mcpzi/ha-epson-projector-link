"""Constants for the epson integration."""

from datetime import timedelta

from .projector.const import PROPERTY_AUTO_IRIS_MODE
from .projector.const import PROPERTY_COLOR_MODE
from .projector.const import PROPERTY_ERR
from .projector.const import PROPERTY_FOCUS
from .projector.const import PROPERTY_LAMP_HOURS
from .projector.const import PROPERTY_LENS_SHIFT_HORIZONTAL
from .projector.const import PROPERTY_LENS_SHIFT_VERTICAL
from .projector.const import PROPERTY_MUTE
from .projector.const import PROPERTY_POWER_CONSUMPTION_MODE
from .projector.const import PROPERTY_SOURCE
from .projector.const import PROPERTY_VOLUME
from .projector.const import PROPERTY_ZOOM

DOMAIN = "epson_projector_link"

MANUFACTURER = "Epson"
MODEL = "Home Cinema Projector"

CONF_POLL_PROPERTIES = "poll_properties"
CONF_PROPERTIES_SCAN_INTERVAL = "poll_properties_scan_interval"

DEFAULT_POWER_SCAN_INTERVAL = 600
DEFAULT_PROPERTIES_SCAN_INTERVAL = 60
POWER_TIMEOUT_RETRY_INTERVAL = timedelta(seconds=10)

# Update error messages in strings.json and translations/en.json
PROPERTY_TO_ATTRIBUTE_NAME_MAP = {
    PROPERTY_AUTO_IRIS_MODE: "auto_iris_mode",
    PROPERTY_COLOR_MODE: "color_mode",
    PROPERTY_ERR: "error",
    PROPERTY_FOCUS: "focus",
    PROPERTY_LAMP_HOURS: "lamp_hours",
    PROPERTY_LENS_SHIFT_HORIZONTAL: "lens_shift_horizontal",
    PROPERTY_LENS_SHIFT_VERTICAL: "lens_shift_vertical",
    PROPERTY_MUTE: "is_volume_muted",
    PROPERTY_POWER_CONSUMPTION_MODE: "power_consumption_mode",
    PROPERTY_SOURCE: "source",
    PROPERTY_VOLUME: "volume",
    PROPERTY_ZOOM: "zoom",
}

STATE_ERROR = "error"

SERVICE_LOAD_LENS_MEMORY = "load_lens_memory"
SERVICE_LOAD_PICTURE_MEMORY = "load_picture_memory"
SERVICE_PUSH_PICTURE_MEMORY = "push_picture_memory"
SERVICE_ERASE_PICTURE_MEMORY = "erase_picture_memory"
SERVICE_SEND_COMMAND = "send_command"
