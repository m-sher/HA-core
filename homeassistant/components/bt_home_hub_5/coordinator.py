"""DataUpdateCoordinator for the BT Home Hub 5 integration."""

from datetime import timedelta
import logging
from typing import override

import bthomehub5_devicelist

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type BtHomeHub5ConfigEntry = ConfigEntry[BtHomeHub5DataUpdateCoordinator]


def get_bt_home_hub_5_data(host: str) -> dict[str, str] | None:
    """Retrieve data from BT Home Hub 5 and return parsed result."""
    return bthomehub5_devicelist.get_devicelist(host)


class BtHomeHub5DataUpdateCoordinator(DataUpdateCoordinator[dict[str, str]]):
    """Class to manage fetching data from the BT Home Hub 5."""

    config_entry: BtHomeHub5ConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: BtHomeHub5ConfigEntry
    ) -> None:
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
    async def _async_update_data(self) -> dict[str, str]:
        """Fetch connected devices from the BT Home Hub 5, keyed by MAC address."""
        if (
            data := await self.hass.async_add_executor_job(
                get_bt_home_hub_5_data, self.host
            )
        ) is None:
            raise UpdateFailed(f"Failed to fetch data from BT Home Hub 5 {self.host}")
        return data
