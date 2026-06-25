"""DataUpdateCoordinator for the Thomson integration."""

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import override

import telnetlib  # pylint: disable=deprecated-module

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEVICES_REGEX, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type ThomsonConfigEntry = ConfigEntry[ThomsonDataUpdateCoordinator]


@dataclass(slots=True, frozen=True)
class ThomsonDevice:
    """Device connected to the Thomson router."""

    mac: str
    ip: str
    host: str | None
    status: str


def get_thomson_data(
    host: str, username: str, password: str
) -> dict[str, ThomsonDevice] | None:
    """Retrieve data from THOMSON and return parsed result."""
    try:
        telnet = telnetlib.Telnet(host)
        telnet.read_until(b"Username : ")
        telnet.write((username + "\r\n").encode("ascii"))
        telnet.read_until(b"Password : ")
        telnet.write((password + "\r\n").encode("ascii"))
        telnet.read_until(b"=>")
        telnet.write(b"hostmgr list\r\n")
        devices_result = telnet.read_until(b"=>").split(b"\r\n")
        telnet.write(b"exit\r\n")
    except EOFError:
        _LOGGER.exception("Unexpected response from router")
        return None
    except OSError:
        _LOGGER.exception("Could not connect to router. Telnet enabled?")
        return None

    devices: dict[str, ThomsonDevice] = {}
    for device in devices_result:
        if match := DEVICES_REGEX.search(device.decode("utf-8")):
            mac = match.group("mac").upper()
            devices[mac] = ThomsonDevice(
                mac=mac,
                ip=match.group("ip"),
                host=match.group("host"),
                status=match.group("status"),
            )
    return devices


class ThomsonDataUpdateCoordinator(DataUpdateCoordinator[dict[str, ThomsonDevice]]):
    """Class to manage fetching data from the Thomson router."""

    config_entry: ThomsonConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ThomsonConfigEntry) -> None:
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
    async def _async_update_data(self) -> dict[str, ThomsonDevice]:
        """Fetch connected devices from the Thomson router."""
        if (
            devices := await self.hass.async_add_executor_job(
                get_thomson_data, self.host, self.username, self.password
            )
        ) is None:
            raise UpdateFailed(f"Failed to fetch data from Thomson router {self.host}")
        # Flag C stands for CONNECTED
        return {
            mac: device
            for mac, device in devices.items()
            if "C" in device.status
        }
