"""Data update coordinator for the FortiOS integration."""

from datetime import timedelta
import logging
from typing import override

from awesomeversion import AwesomeVersion
from fortiosapi import FortiOSAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_TOKEN, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_VERIFY_SSL, DOMAIN, MINIMUM_VERSION

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type FortiOSConfigEntry = ConfigEntry[FortiOSDataUpdateCoordinator]


def create_fortios_api(host: str, token: str, verify_ssl: bool) -> FortiOSAPI | None:
    """Create and authenticate a FortiOS API client."""
    fgt = FortiOSAPI()
    try:
        fgt.tokenlogin(host, token, verify_ssl, None, 12, "root")
    except ConnectionError as ex:
        _LOGGER.error("ConnectionError to FortiOS API: %s", ex)
        return None
    except Exception as ex:  # noqa: BLE001
        _LOGGER.error("Failed to login to FortiOS API: %s", ex)
        return None

    status_json = fgt.monitor("system/status", "")
    current_version = AwesomeVersion(status_json["version"])
    minimum_version = AwesomeVersion(MINIMUM_VERSION)
    if current_version < minimum_version:
        _LOGGER.error(
            "Unsupported FortiOS version: %s. Version %s and newer are supported",
            current_version,
            minimum_version,
        )
        return None
    return fgt


def get_fortios_devices(fgt: FortiOSAPI) -> dict[str, str | None]:
    """Retrieve connected devices from FortiOS."""
    clients_json = fgt.monitor(
        "user/device/query",
        "",
        parameters={"filter": "format=master_mac|hostname|is_online"},
    )

    devices: dict[str, str | None] = {}
    if not clients_json:
        return devices

    try:
        for client in clients_json["results"]:
            if (
                "is_online" in client
                and "master_mac" in client
                and client["is_online"]
            ):
                mac = format_mac(client["master_mac"])
                if "hostname" in client:
                    name = client["hostname"]
                else:
                    name = mac.replace(":", "_")
                devices[mac] = name
    except KeyError as kex:
        _LOGGER.error("Key not found in clients: %s", kex)

    return devices


class FortiOSDataUpdateCoordinator(DataUpdateCoordinator[dict[str, str | None]]):
    """Class to manage fetching data from FortiOS."""

    config_entry: FortiOSConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: FortiOSConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.token = config_entry.data[CONF_TOKEN]
        self.verify_ssl = config_entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        self._fgt: FortiOSAPI | None = None
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    def _get_api(self) -> FortiOSAPI | None:
        """Return an authenticated FortiOS API client."""
        if self._fgt is None:
            self._fgt = create_fortios_api(self.host, self.token, self.verify_ssl)
        return self._fgt

    @override
    async def _async_update_data(self) -> dict[str, str | None]:
        """Fetch connected devices from FortiOS."""
        fgt = await self.hass.async_add_executor_job(self._get_api)
        if fgt is None:
            raise UpdateFailed(f"Failed to connect to FortiOS at {self.host}")
        return await self.hass.async_add_executor_job(get_fortios_devices, fgt)
