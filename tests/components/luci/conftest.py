"""Common fixtures for the OpenWrt (luci) integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.luci.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.1"
MOCK_USERNAME = "root"
MOCK_PASSWORD = "password"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
}

MOCK_DEVICES = {
    "AA:BB:CC:DD:EE:FF": {"mac": "AA:BB:CC:DD:EE:FF", "hostname": "my-phone", "ip": "192.168.1.10"},
    "11:22:33:44:55:66": {"mac": "11:22:33:44:55:66", "hostname": "my-laptop", "ip": "192.168.1.11"},
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.luci.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_luci_router() -> Generator[MagicMock]:
    """Mock Luci router client."""
    mock_router = MagicMock()
    with (
        patch(
            "homeassistant.components.luci.coordinator.create_luci_router",
            return_value=mock_router,
        ),
        patch(
            "homeassistant.components.luci.config_flow.create_luci_router",
            return_value=mock_router,
        ),
        patch(
            "homeassistant.components.luci.coordinator.get_luci_devices",
            return_value=MOCK_DEVICES,
        ),
    ):
        yield mock_router
