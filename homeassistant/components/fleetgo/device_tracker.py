"""Support for FleetGO Platform."""

from typing import Any, override

import voluptuous as vol

from homeassistant.components.device_tracker import (
    PLATFORM_SCHEMA as DEVICE_TRACKER_PLATFORM_SCHEMA,
    AsyncSeeCallback,
    TrackerEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_INCLUDE,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_validation as cv, issue_registry as ir
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FleetGoConfigEntry, FleetGoDataUpdateCoordinator

PLATFORM_SCHEMA = DEVICE_TRACKER_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_CLIENT_SECRET): cv.string,
        vol.Optional(CONF_INCLUDE, default=[]): vol.All(cv.ensure_list, [cv.string]),
    }
)


async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    _async_see: AsyncSeeCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> bool:
    """Set up the legacy FleetGO device tracker."""
    import_data = {
        CONF_USERNAME: config[CONF_USERNAME],
        CONF_PASSWORD: config[CONF_PASSWORD],
        CONF_CLIENT_ID: config[CONF_CLIENT_ID],
        CONF_CLIENT_SECRET: config[CONF_CLIENT_SECRET],
        CONF_INCLUDE: config.get(CONF_INCLUDE, []),
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
            translation_placeholders={"username": import_data[CONF_USERNAME]},
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
            "integration_title": "FleetGO",
        },
    )
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FleetGoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the FleetGO device tracker from a config entry."""
    coordinator = config_entry.runtime_data
    tracked: set[str] = set()

    @callback
    def _async_add_new_devices() -> None:
        """Add newly discovered vehicles from the coordinator."""
        new_entities: list[FleetGoTrackerEntity] = []
        for plate_id in coordinator.data:
            if plate_id not in tracked:
                tracked.add(plate_id)
                new_entities.append(FleetGoTrackerEntity(coordinator, plate_id))
        if new_entities:
            async_add_entities(new_entities)

    config_entry.async_on_unload(coordinator.async_add_listener(_async_add_new_devices))
    _async_add_new_devices()


class FleetGoTrackerEntity(
    CoordinatorEntity[FleetGoDataUpdateCoordinator], TrackerEntity
):
    """Representation of a FleetGO tracked vehicle."""

    _attr_icon = "mdi:car"

    def __init__(
        self, coordinator: FleetGoDataUpdateCoordinator, plate_id: str
    ) -> None:
        """Initialize the tracked vehicle."""
        super().__init__(coordinator)
        self._plate_id = plate_id
        device = coordinator.data.get(plate_id, {})
        self._attr_name = device.get("license_plate") or plate_id
        self._attr_unique_id = plate_id

    @property
    def _device(self) -> dict[str, Any] | None:
        """Return the current vehicle data."""
        return self.coordinator.data.get(self._plate_id)

    @property
    @override
    def latitude(self) -> float | None:
        """Return latitude value of the vehicle."""
        if device := self._device:
            return device.get("latitude")
        return None

    @property
    @override
    def longitude(self) -> float | None:
        """Return longitude value of the vehicle."""
        if device := self._device:
            return device.get("longitude")
        return None

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes of the vehicle."""
        if device := self._device:
            return device
        return {}
