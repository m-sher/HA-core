"""DataUpdateCoordinator for the Synology SRM integration."""

from datetime import timedelta
import logging
from typing import Any, override

import synology_srm

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type SynologySrmConfigEntry = ConfigEntry[SynologySrmDataUpdateCoordinator]


def create_client(
    host: str,
    port: int,
    username: str,
    password: str,
    https: bool,
    verify_ssl: bool,
) -> synology_srm.Client:
    """Create and configure a Synology SRM client."""
    client = synology_srm.Client(
        host=host,
        port=port,
        username=username,
        password=password,
        https=https,
    )
    if not verify_ssl:
        client.http.disable_https_verify()
    return client


def fetch_devices(client: synology_srm.Client) -> list[dict[str, Any]]:
    """Fetch online devices from the router."""
    return client.core.get_network_nsm_device({"is_online": True})


class SynologySrmDataUpdateCoordinator(
    DataUpdateCoordinator[dict[str, dict[str, Any]]]
):
    """Class to manage fetching data from the Synology SRM router."""

    config_entry: SynologySrmConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: SynologySrmConfigEntry
    ) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.client = create_client(
            host=self.host,
            port=config_entry.data[CONF_PORT],
            username=config_entry.data[CONF_USERNAME],
            password=config_entry.data[CONF_PASSWORD],
            https=config_entry.data[CONF_SSL],
            verify_ssl=config_entry.data[CONF_VERIFY_SSL],
        )
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
            devices = await self.hass.async_add_executor_job(fetch_devices, self.client)
        except synology_srm.http.SynologyException as err:
            raise UpdateFailed(
                f"Failed to fetch data from Synology SRM {self.host}"
            ) from err
        return {device["mac"]: device for device in devices if device.get("mac")}
