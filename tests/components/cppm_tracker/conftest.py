"""Common fixtures for the Aruba ClearPass integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.cppm_tracker.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_CLIENT_ID, CONF_HOST

from tests.common import MockConfigEntry

MOCK_HOST = "clearpass.example.com"
MOCK_CLIENT_ID = "client-id"
MOCK_API_KEY = "api-key"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_CLIENT_ID: MOCK_CLIENT_ID,
    CONF_API_KEY: MOCK_API_KEY,
}

MOCK_DEVICES = {
    "AA:BB:CC:DD:EE:FF": "AA:BB:CC:DD:EE:FF",
    "11:22:33:44:55:66": "11:22:33:44:55:66",
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.cppm_tracker.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_cppm_client() -> Generator[MagicMock]:
    """Mock ClearPass client."""
    mock_client = MagicMock()
    with (
        patch(
            "homeassistant.components.cppm_tracker.coordinator.create_cppm_client",
            return_value=mock_client,
        ),
        patch(
            "homeassistant.components.cppm_tracker.config_flow.create_cppm_client",
            return_value=mock_client,
        ),
        patch(
            "homeassistant.components.cppm_tracker.coordinator.get_cppm_devices",
            return_value=MOCK_DEVICES,
        ),
    ):
        yield mock_client
