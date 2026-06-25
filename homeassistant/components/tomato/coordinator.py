"""DataUpdateCoordinator for the Tomato integration."""

from dataclasses import dataclass
from datetime import timedelta
from http import HTTPStatus
import json
import logging
import re
from typing import Any, override

import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_HTTP_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)
PARSE_API_PATTERN = re.compile(r"(?P<param>\w*) = (?P<value>.*);")

type TomatoConfigEntry = ConfigEntry[TomatoDataUpdateCoordinator]


@dataclass(slots=True, frozen=True)
class TomatoDevice:
    """Device connected to the Tomato router."""

    mac: str
    hostname: str | None


def _fetch_devices(config: dict[str, Any]) -> dict[str, TomatoDevice]:
    """Fetch connected devices from the Tomato router (blocking)."""
    host = config[CONF_HOST]
    http_id = config[CONF_HTTP_ID]
    port = config.get(CONF_PORT)
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    use_ssl = config.get(CONF_SSL, False)
    verify_ssl = config.get(CONF_VERIFY_SSL, True)
    if port is None:
        port = 443 if use_ssl else 80

    protocol = "https" if use_ssl else "http"
    req = requests.Request(
        "POST",
        f"{protocol}://{host}:{port}/update.cgi",
        data={"_http_id": http_id, "exec": "devlist"},
        auth=requests.auth.HTTPBasicAuth(username, password),
    ).prepare()

    try:
        if use_ssl:
            response = requests.Session().send(req, timeout=60, verify=verify_ssl)
        else:
            response = requests.Session().send(req, timeout=60)
    except requests.exceptions.ConnectionError as err:
        raise ConnectionError("Failed to connect to the router") from err
    except requests.exceptions.Timeout as err:
        raise ConnectionError("Connection to the router timed out") from err

    if response.status_code == HTTPStatus.UNAUTHORIZED:
        raise ConnectionError("Failed to authenticate")
    if response.status_code != HTTPStatus.OK:
        raise ConnectionError(f"Unexpected status code {response.status_code}")

    last_results: dict[str, list] = {"wldev": [], "dhcpd_lease": []}
    try:
        for param, value in PARSE_API_PATTERN.findall(response.text):
            if param in ("wldev", "dhcpd_lease"):
                last_results[param] = json.loads(value.replace("'", '"'))
    except ValueError as err:
        raise ConnectionError("Failed to parse response from router") from err

    # Build MAC -> hostname from dhcp leases
    hostnames: dict[str, str] = {}
    for item in last_results["dhcpd_lease"]:
        if len(item) >= 3 and item[0] and item[2]:
            hostnames[item[2]] = item[0]

    devices: dict[str, TomatoDevice] = {}
    for item in last_results["wldev"]:
        if len(item) >= 2 and item[1]:
            mac = item[1]
            devices[mac] = TomatoDevice(mac=mac, hostname=hostnames.get(mac))
    return devices


class TomatoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, TomatoDevice]]):
    """Class to manage fetching data from the Tomato router."""

    config_entry: TomatoConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: TomatoConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> dict[str, TomatoDevice]:
        """Fetch connected devices from the Tomato router."""
        try:
            return await self.hass.async_add_executor_job(
                _fetch_devices, dict(self.config_entry.data)
            )
        except ConnectionError as err:
            raise UpdateFailed(str(err)) from err
