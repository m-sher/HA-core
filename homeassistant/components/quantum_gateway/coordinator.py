"""DataUpdateCoordinator for the Quantum Gateway integration."""

from datetime import timedelta
import logging
from typing import override

from quantum_gateway import QuantumGatewayScanner
from requests.exceptions import RequestException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type QuantumGatewayConfigEntry = ConfigEntry[QuantumGatewayDataUpdateCoordinator]


def _fetch_devices(
    host: str, password: str, use_https: bool
) -> dict[str, str | None]:
    """Fetch connected devices from the Quantum Gateway (blocking)."""
    try:
        quantum = QuantumGatewayScanner(host, password, use_https)
    except RequestException as err:
        raise ConnectionError(f"Unable to connect to gateway {host}") from err
    if not quantum.success_init:
        raise ConnectionError(f"Unable to login to gateway {host}")
    try:
        macs = quantum.scan_devices()
    except RequestException as err:
        raise ConnectionError(f"Unable to scan devices on gateway {host}") from err
    return {mac: quantum.get_device_name(mac) for mac in macs}


class QuantumGatewayDataUpdateCoordinator(
    DataUpdateCoordinator[dict[str, str | None]]
):
    """Class to manage fetching data from the Quantum Gateway."""

    config_entry: QuantumGatewayConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: QuantumGatewayConfigEntry
    ) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.password = config_entry.data[CONF_PASSWORD]
        self.use_https = config_entry.data.get(CONF_SSL, True)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> dict[str, str | None]:
        """Fetch connected devices from the Quantum Gateway."""
        try:
            return await self.hass.async_add_executor_job(
                _fetch_devices, self.host, self.password, self.use_https
            )
        except ConnectionError as err:
            raise UpdateFailed(str(err)) from err
