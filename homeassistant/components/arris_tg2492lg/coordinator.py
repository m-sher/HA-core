"""DataUpdateCoordinator for the Arris TG2492LG integration."""

from datetime import timedelta
import logging
from typing import override

from aiohttp.client_exceptions import ClientResponseError
from arris_tg2492lg import ConnectBox, Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type ArrisTg2492lgConfigEntry = ConfigEntry[ArrisTg2492lgDataUpdateCoordinator]


class ArrisTg2492lgDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Device]]):
    """Class to manage fetching data from the Arris TG2492LG router."""

    config_entry: ArrisTg2492lgConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: ArrisTg2492lgConfigEntry
    ) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        url = f"http://{self.host}"
        self.connect_box = ConnectBox(
            async_get_clientsession(hass), url, config_entry.data[CONF_PASSWORD]
        )
        self._logged_in = False
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} - {self.host}",
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> dict[str, Device]:
        """Fetch the connected devices from the Arris TG2492LG router, keyed by MAC address."""
        try:
            if not self._logged_in:
                await self.connect_box.async_login()
                self._logged_in = True
            result = await self.connect_box.async_get_connected_devices()
        except ClientResponseError as err:
            self._logged_in = False
            raise UpdateFailed(
                f"Failed to fetch data from Arris TG2492LG {self.host}"
            ) from err

        devices: dict[str, Device] = {}
        for device in result:
            if device.online and device.mac and device.mac not in devices:
                devices[device.mac] = device
        return devices
