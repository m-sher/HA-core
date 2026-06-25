"""DataUpdateCoordinator for the BT Smart Hub integration."""

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import override

from btsmarthub_devicelist import BTSmartHub

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SMARTHUB_MODEL, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type BTSmartHubConfigEntry = ConfigEntry[BTSmartHubDataUpdateCoordinator]


@dataclass(slots=True, frozen=True)
class BTSmartHubDevice:
    """Device connected to the BT Smart Hub."""

    mac: str
    ip_address: str | None
    host: str | None
    name: str | None


def _fetch_devices(host: str, smarthub_model: int | None) -> dict[str, BTSmartHubDevice]:
    """Fetch connected devices from the BT Smart Hub (blocking)."""
    client = BTSmartHub(router_ip=host, smarthub_model=smarthub_model)
    data = client.get_devicelist(only_active_devices=True)
    if data is None:
        raise ConnectionError(f"Failed to fetch data from BT Smart Hub {host}")
    devices: dict[str, BTSmartHubDevice] = {}
    for item in data:
        mac = item.get("PhysAddress")
        if not mac:
            continue
        devices[mac] = BTSmartHubDevice(
            mac=mac,
            ip_address=item.get("IPAddress"),
            host=item.get("UserHostName"),
            name=item.get("name"),
        )
    return devices


class BTSmartHubDataUpdateCoordinator(
    DataUpdateCoordinator[dict[str, BTSmartHubDevice]]
):
    """Class to manage fetching data from the BT Smart Hub."""

    config_entry: BTSmartHubConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: BTSmartHubConfigEntry
    ) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.smarthub_model = config_entry.data.get(CONF_SMARTHUB_MODEL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> dict[str, BTSmartHubDevice]:
        """Fetch connected devices from the BT Smart Hub."""
        try:
            return await self.hass.async_add_executor_job(
                _fetch_devices, self.host, self.smarthub_model
            )
        except ConnectionError as err:
            raise UpdateFailed(str(err)) from err
