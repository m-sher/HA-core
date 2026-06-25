"""Common fixtures for the Linksys Smart Wi-Fi integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.linksys_smart.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.1"

MOCK_CONFIG = {CONF_HOST: MOCK_HOST}

MOCK_DEVICES = {
    "AA:BB:CC:DD:EE:FF": "my-phone",
    "11:22:33:44:55:66": "my-laptop",
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.linksys_smart.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_get_linksys_smart_data() -> Generator[MagicMock]:
    """Mock Linksys Smart Wi-Fi data fetching."""
    mock_get_data = MagicMock(return_value=MOCK_DEVICES)
    with (
        patch(
            "homeassistant.components.linksys_smart.coordinator.get_linksys_smart_data",
            new=mock_get_data,
        ),
        patch(
            "homeassistant.components.linksys_smart.config_flow.get_linksys_smart_data",
            new=mock_get_data,
        ),
    ):
        yield mock_get_data
