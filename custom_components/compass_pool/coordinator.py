"""Data update coordinator for Compass WiFi pool heater."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CompassApi, CompassApiError
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class CompassCoordinator(DataUpdateCoordinator):
    """Coordinator to poll device status from Compass cloud API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: CompassApi,
        thermostat_key: str,
        device_info: dict,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{thermostat_key}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.thermostat_key = thermostat_key
        self.device_info = device_info

    async def _async_update_data(self) -> dict:
        """Fetch latest device data from the API."""
        try:
            detail = await self.api.get_device_detail(self.thermostat_key)
            return detail
        except CompassApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
