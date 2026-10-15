"""Data update coordinators for Epson Projector Link."""

import asyncio
import logging

from homeassistant.const import STATE_ON
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN
from .const import POWER_TIMEOUT_RETRY_INTERVAL
from .projector.const import PROPERTY_POWER
from .projector.const import PROPERTY_SOURCE
from .projector.const import PROPERTY_SOURCE_LIST

_LOGGER = logging.getLogger(__name__)


class EpsonProjectorPowerCoordinator(DataUpdateCoordinator):
    """Coordinator for the projector power state.

    Power state changes are normally pushed by the projector. This coordinator
    polls as a fallback and to detect the projector coming back online.
    """

    def __init__(self, hass, config_entry, projector, update_interval):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} power",
            update_interval=update_interval,
        )
        self._projector = projector

    async def _async_update_data(self):
        try:
            return await self._projector.get_property(PROPERTY_POWER)
        except asyncio.TimeoutError as err:
            async_call_later(self.hass, POWER_TIMEOUT_RETRY_INTERVAL, self._async_retry)
            raise UpdateFailed("Timed out getting power state") from err
        except Exception as err:
            raise UpdateFailed(f"Error getting power state: {err}") from err

    async def _async_retry(self, now=None):
        await self.async_request_refresh()

    def handle_push_update(self, value):
        """Handle a power state pushed from the projector."""
        self.async_set_updated_data(value)


class EpsonProjectorPropertiesCoordinator(DataUpdateCoordinator):
    """Coordinator for additional projector properties.

    Properties are only actively polled while the projector is powered on.
    """

    def __init__(
        self,
        hass,
        config_entry,
        projector,
        power_coordinator,
        properties,
        update_interval,
    ):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} properties",
            update_interval=update_interval,
        )
        self._projector = projector
        self._power_coordinator = power_coordinator
        self._properties = properties
        self._source_list_fetched = False
        self.data = {}

    async def _async_update_data(self):
        data = dict(self.data)

        if PROPERTY_SOURCE in self._properties and not self._source_list_fetched:
            source_list = await self._async_try_get_property(PROPERTY_SOURCE_LIST)
            if source_list is not None:
                data[PROPERTY_SOURCE_LIST] = source_list
                self._source_list_fetched = True

        if self._power_coordinator.data == STATE_ON:
            for prop in self._properties:
                value = await self._async_try_get_property(prop)
                if value is not None:
                    data[prop] = value

        return data

    async def _async_try_get_property(self, prop):
        try:
            return await self._projector.get_property(prop)
        except Exception as err:
            _LOGGER.warning(
                "Error getting property=%s. Projector may not support it: %s",
                prop,
                err,
            )
            return None

    def handle_push_update(self, prop, value):
        """Handle a property value pushed from the projector."""
        data = dict(self.data)
        data[prop] = value
        self.async_set_updated_data(data)
