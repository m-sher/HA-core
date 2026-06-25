"""Data update coordinator for the OpenWrt (luci) integration."""

from datetime import timedelta
import logging
from typing import Any, override

from openwrt_luci_rpc import OpenWrtRpc

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SSL, DEFAULT_VERIFY_SSL, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type LuciConfigEntry = ConfigEntry[LuciDataUpdateCoordinator]


def create_luci_router(
    host: str,
    username: str,
    password: str,
    ssl: bool = DEFAULT_SSL,
    verify_ssl: bool = DEFAULT_VERIFY_SSL,
) -> OpenWrtRpc | None:
    """Create and authenticate an OpenWrt Luci RPC client."""
    router = OpenWrtRpc(host, username, password, ssl, verify_ssl)
    if not router.is_logged_in():
        return None
    return router


def get_luci_devices(router: OpenWrtRpc) -> dict[str, dict[str, Any]]:
    """Retrieve connected devices from OpenWrt Luci."""
    result = router.get_all_connected_devices(only_reachable=True)
    _LOGGER.debug("Luci get_all_connected_devices returned: %s", result)

    devices: dict[str, dict[str, Any]] = {}
    for device in result:
        if (
            not hasattr(router.router.owrt_version, "release")
            or not router.router.owrt_version.release
            or router.router.owrt_version.release[0] < 19
            or device.reachable
        ):
            devices[device.mac] = device._asdict()
    return devices


class LuciDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Class to manage fetching data from OpenWrt Luci."""

    config_entry: LuciConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: LuciConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data[CONF_PASSWORD]
        self.ssl = config_entry.data.get(CONF_SSL, DEFAULT_SSL)
        self.verify_ssl = config_entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        self._router: OpenWrtRpc | None = None
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    def _get_router(self) -> OpenWrtRpc | None:
        """Return an authenticated Luci router client."""
        if self._router is None:
            self._router = create_luci_router(
                self.host, self.username, self.password, self.ssl, self.verify_ssl
            )
        return self._router

    @override
    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch connected devices from OpenWrt Luci."""
        router = await self.hass.async_add_executor_job(self._get_router)
        if router is None:
            raise UpdateFailed(f"Failed to connect to OpenWrt router {self.host}")
        return await self.hass.async_add_executor_job(get_luci_devices, router)
