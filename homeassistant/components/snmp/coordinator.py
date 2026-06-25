"""DataUpdateCoordinator for the SNMP device tracker."""

import binascii
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any, override

from pysnmp.error import PySnmpError
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    Udp6TransportTarget,
    UdpTransportTarget,
    UsmUserData,
    bulk_walk_cmd,
    is_end_of_mib,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_AUTH_KEY,
    CONF_BASEOID,
    CONF_COMMUNITY,
    CONF_PRIV_KEY,
    DEFAULT_AUTH_PROTOCOL,
    DEFAULT_COMMUNITY,
    DEFAULT_PORT,
    DEFAULT_PRIV_PROTOCOL,
    DEFAULT_TIMEOUT,
    DEFAULT_VERSION,
    DOMAIN,
    SNMP_VERSIONS,
)
from .util import RequestArgsType, async_create_request_cmd_args

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type SnmpConfigEntry = ConfigEntry[SnmpDataUpdateCoordinator]


async def async_create_target(
    host: str,
) -> UdpTransportTarget | Udp6TransportTarget | None:
    """Create an SNMP transport target for the host."""
    try:
        return await UdpTransportTarget.create(
            (host, DEFAULT_PORT), timeout=DEFAULT_TIMEOUT
        )
    except PySnmpError:
        try:
            return Udp6TransportTarget((host, DEFAULT_PORT), timeout=DEFAULT_TIMEOUT)
        except PySnmpError as err:
            _LOGGER.error("Invalid SNMP host: %s", err)
            return None


def create_auth_data(
    community: str,
    authkey: str | None = None,
    privkey: str | None = None,
) -> UsmUserData | CommunityData:
    """Create SNMP authentication data."""
    if authkey is not None or privkey is not None:
        authproto = DEFAULT_AUTH_PROTOCOL
        privproto = DEFAULT_PRIV_PROTOCOL
        if not authkey:
            authproto = "none"
        if not privkey:
            privproto = "none"
        return UsmUserData(
            community,
            authKey=authkey or None,
            privKey=privkey or None,
            authProtocol=authproto,
            privProtocol=privproto,
        )
    return CommunityData(community, mpModel=SNMP_VERSIONS[DEFAULT_VERSION])


async def async_get_snmp_data(
    request_args: RequestArgsType,
) -> list[dict[str, str]] | None:
    """Fetch MAC addresses from access point via SNMP."""
    devices: list[dict[str, str]] = []
    engine, auth_data, target, context_data, object_type = request_args
    walker = bulk_walk_cmd(
        engine,
        auth_data,
        target,
        context_data,
        0,
        50,
        object_type,
        lexicographicMode=False,
    )
    async for errindication, errstatus, errindex, res in walker:
        if errindication:
            _LOGGER.error("SNMPLIB error: %s", errindication)
            return None
        if errstatus:
            _LOGGER.error(
                "SNMP error: %s at %s",
                errstatus.prettyPrint(),
                (errindex and res[int(errindex) - 1][0]) or "?",
            )
            return None

        for _oid, value in res:
            if not is_end_of_mib(res):
                try:
                    mac = binascii.hexlify(value.asOctets()).decode("utf-8")
                except AttributeError:
                    continue
                _LOGGER.debug("Found MAC address: %s", mac)
                mac = ":".join([mac[i : i + 2] for i in range(0, len(mac), 2)])
                devices.append({"mac": mac})
    return devices


async def async_validate_snmp(hass: HomeAssistant, data: dict[str, Any]) -> bool:
    """Validate SNMP connectivity with the given configuration."""
    target = await async_create_target(data[CONF_HOST])
    if target is None:
        return False
    auth_data = create_auth_data(
        data.get(CONF_COMMUNITY, DEFAULT_COMMUNITY),
        data.get(CONF_AUTH_KEY),
        data.get(CONF_PRIV_KEY),
    )
    request_args = await async_create_request_cmd_args(
        hass, auth_data, target, data[CONF_BASEOID]
    )
    result = await async_get_snmp_data(request_args)
    return result is not None


class SnmpDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, str]]]):
    """Class to manage fetching WiFi associations through SNMP."""

    config_entry: SnmpConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: SnmpConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.baseoid = config_entry.data[CONF_BASEOID]
        self._auth_data = create_auth_data(
            config_entry.data.get(CONF_COMMUNITY, DEFAULT_COMMUNITY),
            config_entry.data.get(CONF_AUTH_KEY),
            config_entry.data.get(CONF_PRIV_KEY),
        )
        self._target: UdpTransportTarget | Udp6TransportTarget | None = None
        self.request_args: RequestArgsType | None = None
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    async def async_setup(self) -> None:
        """Set up transport target and request arguments."""
        self._target = await async_create_target(self.host)
        if self._target is None:
            raise UpdateFailed(f"Invalid SNMP host: {self.host}")
        self.request_args = await async_create_request_cmd_args(
            self.hass, self._auth_data, self._target, self.baseoid
        )

    @override
    async def _async_update_data(self) -> dict[str, dict[str, str]]:
        """Fetch MAC addresses from the access point via SNMP."""
        if TYPE_CHECKING:
            assert self.request_args is not None
        data = await async_get_snmp_data(self.request_args)
        if data is None:
            raise UpdateFailed(f"Failed to fetch SNMP data from {self.host}")
        return {client["mac"]: client for client in data if client.get("mac")}
