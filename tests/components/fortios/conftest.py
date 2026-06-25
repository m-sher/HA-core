"""Common fixtures for the FortiOS integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.fortios.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_TOKEN

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.99"
MOCK_TOKEN = "test-token"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_TOKEN: MOCK_TOKEN,
}

MOCK_DEVICES = {
    "AA:BB:CC:DD:EE:FF": "my-phone",
    "11:22:33:44:55:66": "my-laptop",
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.fortios.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_fortios_api() -> Generator[MagicMock]:
    """Mock FortiOS API."""
    mock_api = MagicMock()
    with (
        patch(
            "homeassistant.components.fortios.coordinator.create_fortios_api",
            return_value=mock_api,
        ),
        patch(
            "homeassistant.components.fortios.config_flow.create_fortios_api",
            return_value=mock_api,
        ),
        patch(
            "homeassistant.components.fortios.coordinator.get_fortios_devices",
            return_value=MOCK_DEVICES,
        ),
    ):
        yield mock_api
