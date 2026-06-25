"""DataUpdateCoordinator for the OpenWrt (ubus) integration."""

from datetime import timedelta
import logging
from typing import Any, override

from openwrt.ubus import Ubus

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_DHCP_SOFTWARE, DEFAULT_DHCP_SOFTWARE, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type UbusConfigEntry = ConfigEntry[UbusDataUpdateCoordinator]


def create_ubus(host: str, username: str, password: str) -> Ubus:
    """Create a Ubus client."""
    return Ubus(f"http://{host}/ubus", username, password)


def connect_ubus(ubus: Ubus) -> bool:
    """Connect to the router and return True on success."""
    return ubus.connect() is not None


def _refresh_on_access_denied(func):
    """If router rebooted, rebuild session and try again."""

    def decorator(self, *args, **kwargs):
        """Wrap the function to refresh session_id on PermissionError."""
        try:
            return func(self, *args, **kwargs)
        except PermissionError:
            _LOGGER.warning(
                "Invalid session detected. Trying to refresh session_id and re-run RPC"
            )
            self.ubus.connect()
            return func(self, *args, **kwargs)

    return decorator


class UbusDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Class to manage fetching data from an OpenWrt router via ubus."""

    config_entry: UbusConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: UbusConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.dhcp_software = config_entry.data.get(
            CONF_DHCP_SOFTWARE, DEFAULT_DHCP_SOFTWARE
        )
        self.ubus = create_ubus(
            self.host,
            config_entry.data[CONF_USERNAME],
            config_entry.data[CONF_PASSWORD],
        )
        self.hostapd: list[str] = []
        self._mac2name: dict[str, str] = {}
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
        try:
            devices = await self.hass.async_add_executor_job(self._scan_devices)
        except Exception as err:
            raise UpdateFailed(
                f"Failed to fetch data from OpenWrt router {self.host}"
            ) from err
        if devices is None:
            raise UpdateFailed(f"Failed to fetch data from OpenWrt router {self.host}")
        return devices

    @_refresh_on_access_denied
    def _scan_devices(self) -> dict[str, dict[str, Any]] | None:
        """Scan for connected wireless clients."""
        if not self.hostapd:
            hostapd = self.ubus.get_hostapd()
            if not hostapd:
                return None
            self.hostapd.extend(hostapd.keys())

        devices: dict[str, dict[str, Any]] = {}
        results = 0
        for hostapd in self.hostapd:
            if result := self.ubus.get_hostapd_clients(hostapd):
                results += 1
                for key in result["clients"]:
                    device = result["clients"][key]
                    if device["authorized"]:
                        devices[key] = {
                            "mac": key,
                            "hostname": self._get_device_name(key),
                            "host": self.host,
                        }
        if not results:
            return None
        return devices

    @_refresh_on_access_denied
    def _get_device_name(self, device: str) -> str | None:
        """Return the name of the given device."""
        if not self._mac2name:
            self._generate_mac2name()
        return self._mac2name.get(device.upper())

    @_refresh_on_access_denied
    def _generate_mac2name(self) -> None:
        """Build MAC to hostname mapping from DHCP leases."""
        if self.dhcp_software == "dnsmasq":
            self._generate_mac2name_dnsmasq()
        elif self.dhcp_software == "odhcpd":
            self._generate_mac2name_odhcpd()

    def _generate_mac2name_dnsmasq(self) -> None:
        """Build MAC to name mapping from dnsmasq leases."""
        leasefile = None
        if result := self.ubus.get_uci_config("dhcp", "dnsmasq"):
            values = result["values"].values()
            leasefile = next(iter(values))["leasefile"]
        if not leasefile:
            return
        if not (result := self.ubus.file_read(leasefile)):
            return
        for line in result["data"].splitlines():
            hosts = line.split(" ")
            if len(hosts) >= 4:
                self._mac2name[hosts[1].upper()] = hosts[3]

    def _generate_mac2name_odhcpd(self) -> None:
        """Build MAC to name mapping from odhcpd leases."""
        if not (result := self.ubus.get_dhcp_method("ipv4leases")):
            return
        for device in result["device"].values():
            for lease in device["leases"]:
                mac = lease["mac"]
                mac = ":".join(mac[i : i + 2] for i in range(0, len(mac), 2))
                self._mac2name[mac.upper()] = lease["hostname"]
