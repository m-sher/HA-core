"""DataUpdateCoordinator for the Linksys Smart Wi-Fi integration."""

from datetime import timedelta
from http import HTTPStatus
import logging
from typing import override

import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_TIMEOUT, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)

type LinksysSmartConfigEntry = ConfigEntry[LinksysSmartDataUpdateCoordinator]


def _make_request(host: str) -> requests.Response:
    """Make a request to the Linksys Smart Wi-Fi router."""
    data = [
        {
            "request": {"sinceRevision": 0},
            "action": "http://linksys.com/jnap/devicelist/GetDevices",
        }
    ]
    headers = {"X-JNAP-Action": "http://linksys.com/jnap/core/Transaction"}
    return requests.post(
        f"http://{host}/JNAP/",
        timeout=DEFAULT_TIMEOUT,
        headers=headers,
        json=data,
    )


def get_linksys_smart_data(host: str) -> dict[str, str] | None:
    """Retrieve data from Linksys Smart Wi-Fi and return parsed result."""
    try:
        response = _make_request(host)
    except requests.RequestException:
        _LOGGER.debug("Could not connect to Linksys Smart Wi-Fi at %s", host)
        return None

    if response.status_code != HTTPStatus.OK:
        _LOGGER.debug(
            "Got HTTP status code %d when getting device list from %s",
            response.status_code,
            host,
        )
        return None

    try:
        data = response.json()
        result = data["responses"][0]
        devices = result["output"]["devices"]
    except (KeyError, IndexError, ValueError):
        _LOGGER.debug("Router returned unexpected response from %s", host)
        return None

    last_results: dict[str, str] = {}
    for device in devices:
        if not (macs := device.get("knownMACAddresses")):
            continue
        mac = macs[-1]
        if not device.get("connections"):
            continue

        name = None
        for prop in device.get("properties", []):
            if prop.get("name") == "userDeviceName":
                name = prop.get("value")
        if not name:
            name = device.get("friendlyName", device.get("deviceID", mac))

        last_results[mac] = name
    return last_results


class LinksysSmartDataUpdateCoordinator(DataUpdateCoordinator[dict[str, str]]):
    """Class to manage fetching data from the Linksys Smart Wi-Fi router."""

    config_entry: LinksysSmartConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: LinksysSmartConfigEntry
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
        """Fetch connected devices from the Linksys Smart Wi-Fi router, keyed by MAC address."""
        if (
            data := await self.hass.async_add_executor_job(
                get_linksys_smart_data, self.host
            )
        ) is None:
            raise UpdateFailed(
                f"Failed to fetch data from Linksys Smart Wi-Fi {self.host}"
            )
        return data
