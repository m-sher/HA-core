"""Data update coordinator for the Aruba ClearPass integration."""

from datetime import timedelta
import logging
from typing import override

from clearpasspy import ClearPass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_CLIENT_ID, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, GRANT_TYPE

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=120)

type CPPMConfigEntry = ConfigEntry[CPPMDataUpdateCoordinator]


def create_cppm_client(host: str, client_id: str, api_key: str) -> ClearPass | None:
    """Create and authenticate a ClearPass client."""
    data = {
        "server": host,
        "grant_type": GRANT_TYPE,
        "secret": api_key,
        "client": client_id,
    }
    cppm = ClearPass(data)
    if cppm.access_token is None:
        return None
    _LOGGER.debug("Successfully received Access Token")
    return cppm


def get_cppm_devices(cppm: ClearPass) -> dict[str, str]:
    """Retrieve online devices from Aruba ClearPass."""
    endpoints = cppm.get_endpoints(100)["_embedded"]["items"]
    devices: dict[str, str] = {}
    for item in endpoints:
        if cppm.online_status(item["mac_address"]):
            mac = item["mac_address"]
            devices[mac] = item["mac_address"]
    _LOGGER.debug("Devices: %s", devices)
    return devices


class CPPMDataUpdateCoordinator(DataUpdateCoordinator[dict[str, str]]):
    """Class to manage fetching data from Aruba ClearPass."""

    config_entry: CPPMConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: CPPMConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.client_id = config_entry.data[CONF_CLIENT_ID]
        self.api_key = config_entry.data[CONF_API_KEY]
        self._cppm: ClearPass | None = None
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    def _get_client(self) -> ClearPass | None:
        """Return an authenticated ClearPass client."""
        if self._cppm is None:
            self._cppm = create_cppm_client(self.host, self.client_id, self.api_key)
        return self._cppm

    @override
    async def _async_update_data(self) -> dict[str, str]:
        """Fetch online devices from Aruba ClearPass."""
        cppm = await self.hass.async_add_executor_job(self._get_client)
        if cppm is None:
            raise UpdateFailed(f"Failed to connect to ClearPass at {self.host}")
        return await self.hass.async_add_executor_job(get_cppm_devices, cppm)
