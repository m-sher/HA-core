"""DataUpdateCoordinator for the Bbox integration."""

from datetime import timedelta
import logging
from typing import override

import pybbox

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, Device

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type BboxConfigEntry = ConfigEntry[BboxDataUpdateCoordinator]


def get_bbox_data(host: str) -> list[Device] | None:
    """Retrieve data from Bbox and return parsed result."""
    try:
        box = pybbox.Bbox(ip=host)
        result = box.get_all_connected_devices()
    except Exception:  # noqa: BLE001
        _LOGGER.debug("Could not connect to Bbox at %s", host)
        return None

    devices: list[Device] = []
    for device in result:
        if device["active"] != 1:
            continue
        devices.append(
            Device(device["macaddress"], device["hostname"], device["ipaddress"])
        )
    return devices


class BboxDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Device]]):
    """Class to manage fetching data from the Bbox router."""

    config_entry: BboxConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: BboxConfigEntry) -> None:
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
    async def _async_update_data(self) -> dict[str, Device]:
        """Fetch connected devices from the Bbox router, keyed by MAC address."""
        if (
            devices := await self.hass.async_add_executor_job(
                get_bbox_data, self.host
            )
        ) is None:
            raise UpdateFailed(f"Failed to fetch data from Bbox {self.host}")
        return {device.mac: device for device in devices}
