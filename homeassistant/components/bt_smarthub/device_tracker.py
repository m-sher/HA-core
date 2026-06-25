"""Support for BT Smart Hub device tracking."""

from typing import override

import voluptuous as vol

from homeassistant.components.device_tracker import (
    PLATFORM_SCHEMA as DEVICE_TRACKER_PLATFORM_SCHEMA,
    AsyncSeeCallback,
    ScannerEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_HOST
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_validation as cv, issue_registry as ir
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SMARTHUB_MODEL, DEFAULT_HOST, DOMAIN
from .coordinator import BTSmartHubConfigEntry, BTSmartHubDataUpdateCoordinator

PLATFORM_SCHEMA = DEVICE_TRACKER_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
        vol.Optional(CONF_SMARTHUB_MODEL): vol.In([1, 2]),
    }
)


async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    _async_see: AsyncSeeCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> bool:
    """Set up the legacy BT Smart Hub device tracker."""
    import_data: dict = {CONF_HOST: config.get(CONF_HOST, DEFAULT_HOST)}
    if CONF_SMARTHUB_MODEL in config:
        import_data[CONF_SMARTHUB_MODEL] = config[CONF_SMARTHUB_MODEL]
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
            "integration_title": "BT Smart Hub",
        },
    )
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: BTSmartHubConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the BT Smart Hub device tracker from a config entry."""
    coordinator = config_entry.runtime_data
    tracked: set[str] = set()

    @callback
    def _async_add_new_devices() -> None:
        """Add newly discovered devices from the coordinator."""
        new_entities: list[BTSmartHubScannerEntity] = []
        for mac in coordinator.data:
            if mac not in tracked:
                tracked.add(mac)
                new_entities.append(BTSmartHubScannerEntity(coordinator, mac))
        if new_entities:
            async_add_entities(new_entities)

    config_entry.async_on_unload(coordinator.async_add_listener(_async_add_new_devices))
    _async_add_new_devices()


class BTSmartHubScannerEntity(
    CoordinatorEntity[BTSmartHubDataUpdateCoordinator], ScannerEntity
):
    """Representation of a device connected to the BT Smart Hub."""

    def __init__(
        self, coordinator: BTSmartHubDataUpdateCoordinator, mac: str
    ) -> None:
        """Initialize the tracked device."""
        super().__init__(coordinator)
        self._mac = mac
        device = coordinator.data.get(mac)
        self._attr_name = (
            (device.name or device.host) if device else None
        ) or mac

    @property
    @override
    def is_connected(self) -> bool:
        """Return true if the device is connected."""
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
        if device := self.coordinator.data.get(self._mac):
            return device.ip_address
        return None

    @property
    @override
    def hostname(self) -> str | None:
        """Return the hostname of the device."""
        if device := self.coordinator.data.get(self._mac):
            return device.name or device.host
        return None
