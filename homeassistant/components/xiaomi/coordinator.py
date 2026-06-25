"""DataUpdateCoordinator for the Xiaomi router integration."""

from datetime import timedelta
from http import HTTPStatus
import logging
from typing import Any, override

import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type XiaomiConfigEntry = ConfigEntry[XiaomiDataUpdateCoordinator]


def get_token(host: str, username: str, password: str) -> str | None:
    """Get authentication token for the given host+username+password."""
    url = f"http://{host}/cgi-bin/luci/api/xqsystem/login"
    data = {"username": username, "password": password}
    try:
        res = requests.post(url, data=data, timeout=5)
    except requests.exceptions.Timeout:
        _LOGGER.exception("Connection to the router timed out")
        return None
    if res.status_code == HTTPStatus.OK:
        try:
            result = res.json()
        except ValueError:
            _LOGGER.exception("Failed to parse response from mi router")
            return None
        try:
            return result["token"]
        except KeyError:
            _LOGGER.exception(
                "Xiaomi token cannot be refreshed, response from "
                "url: [%s] \nwith parameter: [%s] \nwas: [%s]",
                url,
                data,
                result,
            )
            return None

    _LOGGER.error("Invalid response: [%s] at url: [%s] with data [%s]", res, url, data)
    return None


def retrieve_list(host: str, token: str, **kwargs: Any) -> list[dict[str, Any]] | None:
    """Get device list for the given host."""
    url = f"http://{host}/cgi-bin/luci/;stok={token}/api/misystem/devicelist"
    try:
        res = requests.get(url, timeout=10, **kwargs)
    except requests.exceptions.Timeout:
        _LOGGER.exception("Connection to the router timed out at URL %s", url)
        return None
    if res.status_code != HTTPStatus.OK:
        _LOGGER.exception("Connection failed with http code %s", res.status_code)
        return None
    try:
        result = res.json()
    except ValueError:
        _LOGGER.exception("Failed to parse response from mi router")
        return None
    try:
        xiaomi_code = result["code"]
    except KeyError:
        _LOGGER.exception("No field code in response from mi router. %s", result)
        return None
    if xiaomi_code == 0:
        try:
            return result["list"]
        except KeyError:
            _LOGGER.exception("No list in response from mi router. %s", result)
            return None
    _LOGGER.warning(
        "Receive wrong Xiaomi code %s, expected 0 in response %s",
        xiaomi_code,
        result,
    )
    return None


class XiaomiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Class to manage fetching data from a Xiaomi Mi router."""

    config_entry: XiaomiConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: XiaomiConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data[CONF_PASSWORD]
        self.token: str | None = None
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch connected devices from the router, keyed by MAC address."""
        devices = await self.hass.async_add_executor_job(self._fetch_devices)
        if devices is None:
            raise UpdateFailed(f"Failed to fetch data from Xiaomi router {self.host}")
        return devices

    def _fetch_devices(self) -> dict[str, dict[str, Any]] | None:
        """Retrieve and filter online devices."""
        result = self._retrieve_list_with_retry()
        if result is None:
            return None
        devices: dict[str, dict[str, Any]] = {}
        for device_entry in result:
            if int(device_entry.get("online", 0)) == 1 and "mac" in device_entry:
                mac = device_entry["mac"]
                devices[mac] = device_entry
        return devices

    def _retrieve_list_with_retry(self) -> list[dict[str, Any]] | None:
        """Retrieve the device list with a retry if token is invalid."""
        if self.token is None:
            self.token = get_token(self.host, self.username, self.password)
            if self.token is None:
                return None
        result = retrieve_list(self.host, self.token)
        if result is not None:
            return result
        self.token = get_token(self.host, self.username, self.password)
        if self.token is None:
            return None
        return retrieve_list(self.host, self.token)
