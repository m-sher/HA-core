"""Tests for SNMP device tracker entities via config entry."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.snmp.const import CONF_BASEOID, DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.1"
MOCK_BASEOID = "1.3.6.1.2.1.2.2.1.6"
MOCK_CONFIG = {CONF_HOST: MOCK_HOST, CONF_BASEOID: MOCK_BASEOID}
MOCK_MACS = {"aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"}


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock SNMP config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


async def test_entities_created_from_coordinator(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: EntityRegistry,
) -> None:
    """Test device tracker entities are created when coordinator returns MACs."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.snmp.coordinator.SnmpDataUpdateCoordinator.async_setup",
            new_callable=AsyncMock,
        ),
        patch(
            "homeassistant.components.snmp.coordinator.SnmpDataUpdateCoordinator._async_update_data",
            new_callable=AsyncMock,
            return_value=MOCK_MACS,
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entries = [
        entry
        for entry in entity_registry.entities.values()
        if entry.domain == "device_tracker" and entry.platform == DOMAIN
    ]
    assert len(entries) == 2
