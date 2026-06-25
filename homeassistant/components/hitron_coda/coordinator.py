"""Data update coordinator for the Hitron CODA integration."""

from collections import namedtuple
from datetime import timedelta
from http import HTTPStatus
import logging
from typing import override

import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_TYPE, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_TYPE, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

Device = namedtuple("Device", ["mac", "name"])  # noqa: PYI024

type HitronCodaConfigEntry = ConfigEntry[HitronCodaDataUpdateCoordinator]


class HitronCodaClient:
    """Client for the Hitron CODA router web interface."""

    def __init__(
        self, host: str, username: str, password: str, router_type: str
    ) -> None:
        """Initialize the client."""
        self._url = f"http://{host}/data/getConnectInfo.asp"
        self._loginurl = f"http://{host}/goform/login"
        self._username = username
        self._password = password
        self._type = "pwd" if router_type == "shaw" else "pws"
        self._userid: str | None = None

    def _login(self) -> bool:
        """Log in to the router. This is required for subsequent api calls."""
        _LOGGER.debug("Logging in to CODA")

        try:
            data = [("user", self._username), (self._type, self._password)]
            res = requests.post(self._loginurl, data=data, timeout=10)
        except requests.exceptions.Timeout:
            _LOGGER.error("Connection to the router timed out at URL %s", self._url)
            return False
        if res.status_code != HTTPStatus.OK:
            _LOGGER.error("Connection failed with http code %s", res.status_code)
            return False
        try:
            self._userid = res.cookies["userid"]
        except KeyError:
            _LOGGER.error("Failed to log in to router")
            return False
        return True

    def get_devices(self) -> list[Device] | None:
        """Get connected devices from router."""
        _LOGGER.debug("Fetching")

        if self._userid is None and not self._login():
            _LOGGER.error("Could not obtain a user ID from the router")
            return None

        try:
            res = requests.get(self._url, timeout=10, cookies={"userid": self._userid})
        except requests.exceptions.Timeout:
            _LOGGER.error("Connection to the router timed out at URL %s", self._url)
            return None
        if res.status_code != HTTPStatus.OK:
            _LOGGER.error("Connection failed with http code %s", res.status_code)
            return None
        try:
            result = res.json()
        except ValueError:
            _LOGGER.error("Failed to parse response from router")
            return None

        devices: list[Device] = []
        for info in result:
            mac = info["macAddr"]
            name = info["hostName"]
            if mac is None:
                continue
            devices.append(Device(mac.upper(), name))

        _LOGGER.debug("Request successful")
        return devices


def get_hitron_coda_data(
    host: str, username: str, password: str, router_type: str
) -> dict[str, str] | None:
    """Retrieve connected devices from Hitron CODA, keyed by MAC address."""
    client = HitronCodaClient(host, username, password, router_type)
    if (devices := client.get_devices()) is None:
        return None
    return {device.mac: device.name for device in devices}


class HitronCodaDataUpdateCoordinator(DataUpdateCoordinator[dict[str, str]]):
    """Class to manage fetching data from the Hitron CODA router."""

    config_entry: HitronCodaConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: HitronCodaConfigEntry
    ) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data[CONF_PASSWORD]
        self.router_type = config_entry.data.get(CONF_TYPE, DEFAULT_TYPE)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> dict[str, str]:
        """Fetch connected devices from the Hitron CODA router."""
        if (
            devices := await self.hass.async_add_executor_job(
                get_hitron_coda_data,
                self.host,
                self.username,
                self.password,
                self.router_type,
            )
        ) is None:
            raise UpdateFailed(
                f"Failed to fetch data from Hitron CODA router {self.host}"
            )
        return devices
