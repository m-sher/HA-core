"""Data update coordinator for the Aruba integration."""

from datetime import timedelta
import logging
from typing import override

import pexpect

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEVICES_REGEX, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type ArubaConfigEntry = ConfigEntry[ArubaDataUpdateCoordinator]


def get_aruba_data(
    host: str, username: str, password: str
) -> dict[str, dict[str, str]] | None:
    """Retrieve data from Aruba Access Point and return parsed result."""
    connect = f"ssh {username}@{host}"
    ssh: pexpect.spawn[str] = pexpect.spawn(connect, encoding="utf-8")
    query = ssh.expect(
        [
            "password:",
            pexpect.TIMEOUT,
            pexpect.EOF,
            "continue connecting (yes/no)?",
            "Host key verification failed.",
            "Connection refused",
            "Connection timed out",
        ],
        timeout=120,
    )
    if query == 1:
        _LOGGER.error("Timeout")
        return None
    if query == 2:
        _LOGGER.error("Unexpected response from router")
        return None
    if query == 3:
        ssh.sendline("yes")
        ssh.expect("password:")
    elif query == 4:
        _LOGGER.error("Host key changed")
        return None
    elif query == 5:
        _LOGGER.error("Connection refused by server")
        return None
    elif query == 6:
        _LOGGER.error("Connection timed out")
        return None
    ssh.sendline(password)
    ssh.expect("#")
    ssh.sendline("show clients")
    ssh.expect("#")
    devices_result = (ssh.before or "").splitlines()
    ssh.sendline("exit")

    devices: dict[str, dict[str, str]] = {}
    for device in devices_result:
        if match := DEVICES_REGEX.search(device):
            devices[match.group("mac").upper()] = {
                "ip": match.group("ip"),
                "mac": match.group("mac").upper(),
                "name": match.group("name"),
            }
    return devices


class ArubaDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, str]]]):
    """Class to manage fetching data from the Aruba Access Point."""

    config_entry: ArubaConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ArubaConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data[CONF_PASSWORD]
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> dict[str, dict[str, str]]:
        """Fetch connected devices from the Aruba Access Point."""
        if (
            devices := await self.hass.async_add_executor_job(
                get_aruba_data, self.host, self.username, self.password
            )
        ) is None:
            raise UpdateFailed(
                f"Failed to fetch data from Aruba Access Point {self.host}"
            )
        return devices
