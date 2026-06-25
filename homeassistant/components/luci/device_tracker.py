"""Support for OpenWRT (luci) routers."""

from typing import Any, override

import voluptuous as vol

from homeassistant.components.device_tracker import (
    PLATFORM_SCHEMA as DEVICE_TRACKER_PLATFORM_SCHEMA,
    AsyncSeeCallback,
    ScannerEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_validation as cv, issue_registry as ir
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_SSL, DEFAULT_VERIFY_SSL, DOMAIN
from .coordinator import LuciConfigEntry, LuciDataUpdateCoordinator

PLATFORM_SCHEMA = DEVICE_TRACKER_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
    }
)


async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    _async_see: AsyncSeeCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> bool:
    """Set up the legacy OpenWrt (luci) device tracker."""
    import_data = {
        CONF_HOST: config[CONF_HOST],
        CONF_USERNAME: config[CONF_USERNAME],
        CONF_PASSWORD: config[CONF_PASSWORD],
        CONF_SSL: config.get(CONF_SSL, DEFAULT_SSL),
        CONF_VERIFY_SSL: config.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=import_data
    )

    if result["type"] is FlowResultType.ABORT and result["reason"] == "cannot_connect":
        ir.async_create_issue(
            hass,
            DOMAIN,
            "yaml_import_cannot_connect",
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=ir.IssueSeverity.ERROR,
            translation_key="yaml_import_cannot_connect",
            translation_placeholders={"host": import_data[CONF_HOST]},
        )
        return False

    ir.async_delete_issue(hass, DOMAIN, "yaml_import_cannot_connect")
    ir.async_create_issue(
        hass,
        HOMEASSISTANT_DOMAIN,
        f"deprecated_yaml_{DOMAIN}",
        is_fixable=False,
        issue_domain=DOMAIN,
        severity=ir.IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
        translation_placeholders={
            "domain": DOMAIN,
            "integration_title": "OpenWrt (luci)",
        },
    )
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: LuciConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the OpenWrt (luci) device tracker from a config entry."""
    coordinator = config_entry.runtime_data
    tracked: set[str] = set()

    @callback
    def _async_add_new_devices() -> None:
        """Add newly discovered devices from the coordinator."""
        new_entities: list[LuciScannerEntity] = []
        for mac in coordinator.data:
            if mac not in tracked:
                tracked.add(mac)
                new_entities.append(LuciScannerEntity(coordinator, mac))
        if new_entities:
            async_add_entities(new_entities)

    config_entry.async_on_unload(coordinator.async_add_listener(_async_add_new_devices))
    _async_add_new_devices()


class LuciScannerEntity(CoordinatorEntity[LuciDataUpdateCoordinator], ScannerEntity):
    """Representation of a device connected to an OpenWrt router."""

    def __init__(self, coordinator: LuciDataUpdateCoordinator, mac: str) -> None:
        """Initialize the tracked device."""
        super().__init__(coordinator)
        self._mac = mac
        device = coordinator.data.get(mac, {})
        self._attr_name = device.get("hostname") or mac

    @property
    def _device(self) -> dict[str, Any] | None:
        """Return the current device data."""
        return self.coordinator.data.get(self._mac)

    @property
    @override
    def is_connected(self) -> bool:
        """Return true if the device is connected to the OpenWrt router."""
        return self._mac in self.coordinator.data

    @property
    @override
    def mac_address(self) -> str:
        """Return the MAC address of the device."""
        return self._mac

    @property
    @override
    def ip_address(self) -> str | None:
        """Return the IP address of the device."""
        if device := self._device:
            return device.get("ip")
        return None

    @property
    @override
    def hostname(self) -> str | None:
        """Return the hostname of the device."""
        if device := self._device:
            return device.get("hostname")
        return None

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes of the device."""
        if device := self._device:
            return device
        return {}
