"""Data update coordinator for the DD-WRT integration."""

from datetime import timedelta
from http import HTTPStatus
import logging
import re
from typing import override

import requests

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

from .const import CONF_WIRELESS_ONLY, DEFAULT_SSL, DEFAULT_VERIFY_SSL, DEFAULT_WIRELESS_ONLY, DOMAIN

_LOGGER = logging.getLogger(__name__)

_DDWRT_DATA_REGEX = re.compile(r"\{(\w+)::([^\}]*)\}")
_MAC_REGEX = re.compile(r"(([0-9A-Fa-f]{1,2}\:){5}[0-9A-Fa-f]{1,2})")

UPDATE_INTERVAL = timedelta(seconds=30)

type DdWrtConfigEntry = ConfigEntry[DdWrtDataUpdateCoordinator]


def _parse_ddwrt_response(data_str: str) -> dict[str, str]:
    """Parse the DD-WRT data format."""
    return dict(_DDWRT_DATA_REGEX.findall(data_str))


def get_ddwrt_data(
    protocol: str, host: str, username: str, password: str, verify_ssl: bool, url: str
) -> dict[str, str] | None:
    """Retrieve data from DD-WRT and return parsed result."""
    try:
        response = requests.get(
            url,
            auth=(username, password),
            timeout=4,
            verify=verify_ssl,
        )
    except requests.exceptions.Timeout:
        _LOGGER.exception("Connection to the router timed out")
        return None
    if response.status_code == HTTPStatus.OK:
        return _parse_ddwrt_response(response.text)
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        _LOGGER.exception(
            "Failed to authenticate, check your username and password"
        )
        return None
    _LOGGER.error("Invalid response from DD-WRT: %s", response)
    return None


def get_ddwrt_devices(
    host: str,
    username: str,
    password: str,
    ssl: bool = DEFAULT_SSL,
    verify_ssl: bool = DEFAULT_VERIFY_SSL,
    wireless_only: bool = DEFAULT_WIRELESS_ONLY,
) -> dict[str, str | None] | None:
    """Retrieve connected devices from DD-WRT router."""
    protocol = "https" if ssl else "http"
    endpoint = "Wireless" if wireless_only else "Lan"
    url = f"{protocol}://{host}/Status_{endpoint}.live.asp"

    if not (data := get_ddwrt_data(protocol, host, username, password, verify_ssl, url)):
        return None

    if wireless_only:
        active_clients = data.get("active_wireless")
    else:
        active_clients = data.get("arp_table")
    if not active_clients:
        return {}

    clean_str = active_clients.strip().strip("'")
    elements = clean_str.split("','")
    macs = [item for item in elements if _MAC_REGEX.match(item)]

    # Fetch device names from DHCP leases
    lan_url = f"{protocol}://{host}/Status_Lan.live.asp"
    mac2name: dict[str, str] = {}
    if lan_data := get_ddwrt_data(protocol, host, username, password, verify_ssl, lan_url):
        if dhcp_leases := lan_data.get("dhcp_leases"):
            cleaned_str = dhcp_leases.replace('"', "").replace("'", "").replace(" ", "")
            lease_elements = cleaned_str.split(",")
            num_clients = int(len(lease_elements) / 5)
            for idx in range(num_clients):
                mac_index = (idx * 5) + 2
                if mac_index < len(lease_elements):
                    mac = lease_elements[mac_index]
                    mac2name[mac] = lease_elements[idx * 5]

    return {mac: mac2name.get(mac) for mac in macs}


class DdWrtDataUpdateCoordinator(DataUpdateCoordinator[dict[str, str | None]]):
    """Class to manage fetching data from the DD-WRT router."""

    config_entry: DdWrtConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: DdWrtConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data[CONF_PASSWORD]
        self.ssl = config_entry.data.get(CONF_SSL, DEFAULT_SSL)
        self.verify_ssl = config_entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        self.wireless_only = config_entry.data.get(
            CONF_WIRELESS_ONLY, DEFAULT_WIRELESS_ONLY
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> dict[str, str | None]:
        """Fetch connected devices from the DD-WRT router."""
        if (
            devices := await self.hass.async_add_executor_job(
                get_ddwrt_devices,
                self.host,
                self.username,
                self.password,
                self.ssl,
                self.verify_ssl,
                self.wireless_only,
            )
        ) is None:
            raise UpdateFailed(f"Failed to fetch data from DD-WRT router {self.host}")
        return devices
