"""DataUpdateCoordinator for the UPC Connect Box integration."""

from datetime import timedelta
import logging
from typing import Any, override

from connect_box import ConnectBox
from connect_box.exceptions import ConnectBoxError, ConnectBoxLoginError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type UpcConnectConfigEntry = ConfigEntry[UpcConnectDataUpdateCoordinator]


class UpcConnectDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the UPC Connect Box."""

    config_entry: UpcConnectConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: UpcConnectConfigEntry
    ) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.connect_box = ConnectBox(
            async_get_clientsession(hass),
            config_entry.data[CONF_PASSWORD],
            host=self.host,
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the connected devices from the UPC Connect Box, keyed by MAC address."""
        try:
            await self.connect_box.async_get_devices()
        except ConnectBoxLoginError as err:
            raise UpdateFailed(
                f"Login failed for UPC Connect Box {self.host}"
            ) from err
        except ConnectBoxError as err:
            raise UpdateFailed(
                f"Failed to fetch data from UPC Connect Box {self.host}"
            ) from err

        devices: dict[str, Any] = {}
        for device in self.connect_box.devices:
            if device.mac:
                devices[device.mac] = device
        return devices
