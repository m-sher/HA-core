"""Tests for the Aruba ClearPass device tracker."""

from unittest.mock import MagicMock, patch

from homeassistant.components.cppm_tracker.const import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.helpers.issue_registry import IssueRegistry
from homeassistant.setup import async_setup_component

from .conftest import MOCK_CONFIG, MOCK_HOST

from tests.common import MockConfigEntry


async def test_entities_created(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_cppm_client: MagicMock,
    entity_registry: EntityRegistry,
) -> None:
    """Test device tracker entities are created from the coordinator data."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entries = [
        entry
        for entry in entity_registry.entities.values()
        if entry.domain == "device_tracker" and entry.platform == DOMAIN
    ]
    assert len(entries) == 2


async def test_legacy_platform_imports_config_entry(
    hass: HomeAssistant, mock_cppm_client: MagicMock
) -> None:
    """Test the legacy device_tracker platform imports a config entry."""
    assert await async_setup_component(
        hass,
        "device_tracker",
        {"device_tracker": [{"platform": DOMAIN, **MOCK_CONFIG}]},
    )
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].source == SOURCE_IMPORT


async def test_legacy_platform_creates_issue_on_cannot_connect(
    hass: HomeAssistant,
    issue_registry: IssueRegistry,
) -> None:
    """Test an issue is raised when the legacy YAML import cannot connect."""
    with patch(
        "homeassistant.components.cppm_tracker.config_flow.create_cppm_client",
        return_value=None,
    ):
        assert await async_setup_component(
            hass,
            "device_tracker",
            {"device_tracker": [{"platform": DOMAIN, **MOCK_CONFIG}]},
        )
        await hass.async_block_till_done()

    issue = issue_registry.async_get_issue(DOMAIN, "yaml_import_cannot_connect")
    assert issue is not None
    assert issue.translation_placeholders == {"host": MOCK_HOST}


async def test_setup_entry_retries_when_unavailable(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the config entry retries when ClearPass is unavailable."""
    with patch(
        "homeassistant.components.cppm_tracker.coordinator.create_cppm_client",
        return_value=None,
    ):
        mock_config_entry.add_to_hass(hass)
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
