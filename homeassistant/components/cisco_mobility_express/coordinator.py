"""Data update coordinator for the Cisco Mobility Express integration."""

from datetime import timedelta
import logging
from typing import Any, override

from ciscomobilityexpress.ciscome import CiscoMobilityExpress

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SSL, DEFAULT_VERIFY_SSL, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type CiscoMobilityExpressConfigEntry = ConfigEntry[
    CiscoMobilityExpressDataUpdateCoordinator
]


def get_cisco_me_controller(
    host: str, username: str, password: str, use_https: bool, verify_ssl: bool
) -> CiscoMobilityExpress | None:
    """Create and validate a Cisco Mobility Express controller connection."""
    controller = CiscoMobilityExpress(host, username, password, use_https, verify_ssl)
    if not controller.is_logged_in():
        return None
    return controller


def get_cisco_me_data(controller: CiscoMobilityExpress) -> dict[str, dict[str, Any]]:
    """Retrieve associated devices from Cisco ME, keyed by MAC address."""
    devices: dict[str, dict[str, Any]] = {}
    for device in controller.get_associated_devices():
        devices[device.macaddr] = device._asdict()
    return devices


class CiscoMobilityExpressDataUpdateCoordinator(
    DataUpdateCoordinator[dict[str, dict[str, Any]]]
):
    """Class to manage fetching data from the Cisco Mobility Express controller."""

    config_entry: CiscoMobilityExpressConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: CiscoMobilityExpressConfigEntry
    ) -> None:
        """Initialize the coordinator using the config entry."""
        self.host = config_entry.data[CONF_HOST]
        self.controller = CiscoMobilityExpress(
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_USERNAME],
            config_entry.data[CONF_PASSWORD],
            config_entry.data.get(CONF_SSL, DEFAULT_SSL),
            config_entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
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
        """Fetch associated devices from the Cisco Mobility Express controller."""
        try:
            devices = await self.hass.async_add_executor_job(
                get_cisco_me_data, self.controller
            )
        except Exception as err:
            raise UpdateFailed(
                f"Failed to fetch data from Cisco Mobility Express {self.host}"
            ) from err
        _LOGGER.debug("Cisco Mobility Express controller returned: %s", devices)
        return devices
