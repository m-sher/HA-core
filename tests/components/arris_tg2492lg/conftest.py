"""Common fixtures for the Arris TG2492LG integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.arris_tg2492lg.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.178.1"
MOCK_PASSWORD = "password"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_PASSWORD: MOCK_PASSWORD,
}


def _make_device(mac: str, hostname: str, ip: str) -> MagicMock:
    """Create a mock arris Device."""
    device = MagicMock()
    device.mac = mac
    device.hostname = hostname
    device.ip = ip
    device.online = True
    return device


MOCK_DEVICES = [
    _make_device("AA:BB:CC:DD:EE:FF", "my-phone", "192.168.178.10"),
    _make_device("11:22:33:44:55:66", "my-laptop", "192.168.178.11"),
]


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.arris_tg2492lg.async_setup_entry", return_value=True
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
        patch(
            "homeassistant.components.arris_tg2492lg.coordinator.ConnectBox"
        ) as mock,
        patch(
            "homeassistant.components.arris_tg2492lg.config_flow.ConnectBox", new=mock
        ),
    ):
        instance = MagicMock()
        instance.async_login = AsyncMock()
        instance.async_get_connected_devices = AsyncMock(return_value=MOCK_DEVICES)
        mock.return_value = instance
        yield mock
