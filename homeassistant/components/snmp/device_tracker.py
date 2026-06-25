"""Support for fetching WiFi associations through SNMP."""

from typing import Any, override

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

from .const import (
    CONF_AUTH_KEY,
    CONF_BASEOID,
    CONF_COMMUNITY,
    CONF_PRIV_KEY,
    DEFAULT_COMMUNITY,
    DOMAIN,
)
from .coordinator import SnmpConfigEntry, SnmpDataUpdateCoordinator

PLATFORM_SCHEMA = DEVICE_TRACKER_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_BASEOID): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_COMMUNITY, default=DEFAULT_COMMUNITY): cv.string,
        vol.Inclusive(CONF_AUTH_KEY, "keys"): cv.string,
        vol.Inclusive(CONF_PRIV_KEY, "keys"): cv.string,
    }
)


async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    _async_see: AsyncSeeCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> bool:
    """Set up the legacy SNMP device tracker."""
    import_data: dict[str, Any] = {
        CONF_HOST: config[CONF_HOST],
        CONF_BASEOID: config[CONF_BASEOID],
        CONF_COMMUNITY: config.get(CONF_COMMUNITY, DEFAULT_COMMUNITY),
    }
    if CONF_AUTH_KEY in config:
        import_data[CONF_AUTH_KEY] = config[CONF_AUTH_KEY]
    if CONF_PRIV_KEY in config:
        import_data[CONF_PRIV_KEY] = config[CONF_PRIV_KEY]

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
            "integration_title": "SNMP",
        },
    )
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SnmpConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the SNMP device tracker from a config entry."""
    coordinator = config_entry.runtime_data
    tracked: set[str] = set()

    @callback
    def _async_add_new_devices() -> None:
        """Add newly discovered devices from the coordinator."""
        new_entities: list[SnmpScannerEntity] = []
        for mac in coordinator.data:
            if mac not in tracked:
                tracked.add(mac)
                new_entities.append(SnmpScannerEntity(coordinator, mac))
        if new_entities:
            async_add_entities(new_entities)

    config_entry.async_on_unload(coordinator.async_add_listener(_async_add_new_devices))
    _async_add_new_devices()


class SnmpScannerEntity(CoordinatorEntity[SnmpDataUpdateCoordinator], ScannerEntity):
    """Representation of a device discovered via SNMP."""

    def __init__(self, coordinator: SnmpDataUpdateCoordinator, mac: str) -> None:
        """Initialize the tracked device."""
        super().__init__(coordinator)
        self._mac = mac
        self._attr_name = mac

    @property
    @override
    def is_connected(self) -> bool:
        """Return true if the device is present in the latest SNMP scan."""
        return self._mac in self.coordinator.data

    @property
    @override
    def mac_address(self) -> str:
        """Return the MAC address of the device."""
        return self._mac

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes of the device."""
        if self._mac in self.coordinator.data:
            return {"mac": self._mac}
        return None
