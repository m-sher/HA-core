"""Data update coordinator for the Cisco IOS integration."""

from datetime import timedelta
import logging
from typing import override

from pexpect import pxssh

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type CiscoIOSConfigEntry = ConfigEntry[CiscoIOSDataUpdateCoordinator]


def _parse_cisco_mac_address(cisco_hardware_addr: str) -> str:
    """Parse a Cisco formatted HW address to normal MAC."""
    cisco_hardware_addr = cisco_hardware_addr.replace(".", "")
    blocks = [
        cisco_hardware_addr[x : x + 2] for x in range(0, len(cisco_hardware_addr), 2)
    ]
    return ":".join(blocks).upper()


def get_cisco_arp_data(
    host: str, username: str, password: str, port: int | None = None
) -> str | None:
    """Open connection to the router and get arp entries."""
    try:
        cisco_ssh: pxssh.pxssh[str] = pxssh.pxssh(encoding="utf-8")
        cisco_ssh.login(
            host,
            username,
            password,
            port=port,
            auto_prompt_reset=False,
        )

        initial_line = (cisco_ssh.before or "").splitlines()
        router_hostname = initial_line[len(initial_line) - 1]
        router_hostname += "#"
        cisco_ssh.PROMPT = f"(?i)^{router_hostname}"
        cisco_ssh.sendline("terminal length 0")
        cisco_ssh.prompt(1)

        cisco_ssh.sendline("show ip arp")
        cisco_ssh.prompt(1)

    except pxssh.ExceptionPxssh as px_e:
        _LOGGER.error("Failed to login via pxssh: %s", px_e)
        return None

    return cisco_ssh.before


def get_cisco_devices(
    host: str, username: str, password: str, port: int | None = None
) -> list[str] | None:
    """Retrieve recently seen devices from Cisco IOS ARP table."""
    if not (string_result := get_cisco_arp_data(host, username, password, port)):
        return None

    last_results: list[str] = []
    lines_result = string_result.splitlines()[2:]

    for line in lines_result:
        parts = line.split()
        if len(parts) != 6:
            continue

        age = parts[2]
        hw_addr = parts[3]

        if age != "-":
            mac = _parse_cisco_mac_address(hw_addr)
            age_int = int(age)
            if age_int < 1:
                last_results.append(mac)

    return last_results


class CiscoIOSDataUpdateCoordinator(DataUpdateCoordinator[list[str]]):
    """Class to manage fetching data from Cisco IOS."""

    config_entry: CiscoIOSConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: CiscoIOSConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data.get(CONF_PASSWORD, "")
        self.port = config_entry.data.get(CONF_PORT)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> list[str]:
        """Fetch connected devices from Cisco IOS."""
        if (
            devices := await self.hass.async_add_executor_job(
                get_cisco_devices,
                self.host,
                self.username,
                self.password,
                self.port,
            )
        ) is None:
            raise UpdateFailed(f"Failed to fetch data from Cisco IOS router {self.host}")
        return devices
