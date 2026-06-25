"""Common fixtures for the UPC Connect Box integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.upc_connect.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.0.1"
MOCK_PASSWORD = "password"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_PASSWORD: MOCK_PASSWORD,
}


def _make_device(mac: str, hostname: str) -> MagicMock:
    """Create a mock connect_box Device."""
    device = MagicMock()
    device.mac = mac
    device.hostname = hostname
    return device


MOCK_DEVICES = [
    _make_device("AA:BB:CC:DD:EE:FF", "my-phone"),
    _make_device("11:22:33:44:55:66", "my-laptop"),
]


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.upc_connect.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_connect_box() -> Generator[MagicMock]:
    """Mock ConnectBox to return known devices."""
    with (
        patch("homeassistant.components.upc_connect.coordinator.ConnectBox") as mock,
        patch("homeassistant.components.upc_connect.config_flow.ConnectBox", new=mock),
    ):
        instance = MagicMock()
        instance.async_initialize_token = AsyncMock()
        instance.async_get_devices = AsyncMock()
        instance.devices = MOCK_DEVICES
        mock.return_value = instance
        yield mock
