"""Support for Xiaomi Mi WiFi Repeater device tracking."""

from typing import Any, override

import voluptuous as vol

from homeassistant.components.device_tracker import (
    PLATFORM_SCHEMA as DEVICE_TRACKER_PLATFORM_SCHEMA,
    AsyncSeeCallback,
    ScannerEntity,
)
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, issue_registry as ir
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .typing import XiaomiMiioConfigEntry

PLATFORM_SCHEMA = DEVICE_TRACKER_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
    }
)


async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    async_see: AsyncSeeCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> bool:
    """Inform users that the YAML configuration is no longer supported."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml_device_tracker",
        breaks_in_ha_version="2027.1.0",
        is_fixable=False,
        is_persistent=False,
        issue_domain=DOMAIN,
        severity=ir.IssueSeverity.WARNING,
        translation_key="deprecated_yaml_device_tracker",
        translation_placeholders={
            "domain": DOMAIN,
            "integration_title": "Xiaomi Miio",
        },
    )
    return False


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: XiaomiMiioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up device tracker entities for Xiaomi Mi WiFi Repeater."""
    coordinator = config_entry.runtime_data.device_coordinator
    tracked: set[str] = set()

    @callback
    def _async_add_new_devices() -> None:
        """Add newly discovered devices from the coordinator."""
        if coordinator.data is None:
            return
        stations = coordinator.data.associated_stations
        new_entities: list[XiaomiMiioScannerEntity] = []
        for station in stations:
            mac = station["mac"]
            if mac not in tracked:
                tracked.add(mac)
                new_entities.append(XiaomiMiioScannerEntity(coordinator, mac))
        if new_entities:
            async_add_entities(new_entities)

    config_entry.async_on_unload(coordinator.async_add_listener(_async_add_new_devices))
    _async_add_new_devices()


class XiaomiMiioScannerEntity(CoordinatorEntity, ScannerEntity):
    """Representation of a device connected to a Xiaomi Mi WiFi Repeater."""

    def __init__(self, coordinator, mac: str) -> None:
        """Initialize the tracked device."""
        super().__init__(coordinator)
        self._mac = mac
        self._attr_name = mac

    def _get_station(self) -> dict[str, Any] | None:
        """Return station data for this MAC if present."""
        if self.coordinator.data is None:
            return None
        for station in self.coordinator.data.associated_stations:
            if station["mac"] == self._mac:
                return station
        return None

    @property
    @override
    def is_connected(self) -> bool:
        """Return true if the device is connected to the repeater."""
        return self._get_station() is not None

    @property
    @override
    def mac_address(self) -> str:
        """Return the MAC address of the device."""
        return self._mac

    @property
    @override
    def ip_address(self) -> str | None:
        """Return the IP address of the device."""
        if station := self._get_station():
            return station.get("ip")
        return None
