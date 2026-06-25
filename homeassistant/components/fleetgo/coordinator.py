"""Data update coordinator for the FleetGO integration."""

from datetime import timedelta
import logging
from typing import Any, override

import requests
from ritassist import API

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_INCLUDE,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type FleetGoConfigEntry = ConfigEntry[FleetGoDataUpdateCoordinator]


def create_fleetgo_api(
    client_id: str, client_secret: str, username: str, password: str
) -> API | None:
    """Create and authenticate a FleetGO API client."""
    api = API(client_id, client_secret, username, password)
    if not api.login():
        return None
    return api


def get_fleetgo_devices(
    api: API, include: list[str] | None = None
) -> dict[str, dict[str, Any]]:
    """Retrieve vehicle devices from FleetGO."""
    try:
        devices = api.get_devices()
    except requests.exceptions.ConnectionError:
        _LOGGER.error("ConnectionError: Could not connect to FleetGO")
        raise

    result: dict[str, dict[str, Any]] = {}
    for device in devices:
        if not include or device.license_plate in include:
            if device.active or device.current_address is None:
                device.get_map_details()
            result[device.plate_as_id] = device.state_attributes
    return result


class FleetGoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Class to manage fetching data from FleetGO."""

    config_entry: FleetGoConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: FleetGoConfigEntry) -> None:
        """Initialize the coordinator using the config entry."""
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data[CONF_PASSWORD]
        self.client_id = config_entry.data[CONF_CLIENT_ID]
        self.client_secret = config_entry.data[CONF_CLIENT_SECRET]
        self.include: list[str] = config_entry.data.get(CONF_INCLUDE, [])
        self._api: API | None = None
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    def _get_api(self) -> API | None:
        """Return an authenticated FleetGO API client."""
        if self._api is None:
            self._api = create_fleetgo_api(
                self.client_id, self.client_secret, self.username, self.password
            )
        return self._api

    @override
    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch vehicle devices from FleetGO."""
        api = await self.hass.async_add_executor_job(self._get_api)
        if api is None:
            raise UpdateFailed("Failed to authenticate with FleetGO")
        try:
            return await self.hass.async_add_executor_job(
                get_fleetgo_devices, api, self.include or None
            )
        except requests.exceptions.ConnectionError as err:
            raise UpdateFailed("Failed to connect to FleetGO") from err
