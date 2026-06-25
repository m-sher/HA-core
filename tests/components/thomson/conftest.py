"""Common fixtures for the Thomson integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.thomson.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.1"
MOCK_USERNAME = "admin"
MOCK_PASSWORD = "password"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
}

MOCK_DEVICES = {
    "AA:BB:CC:DD:EE:FF": {
        "ip": "192.168.1.10",
        "mac": "AA:BB:CC:DD:EE:FF",
        "host": "my-phone",
        "status": "C",
    },
    "11:22:33:44:55:66": {
        "ip": "192.168.1.11",
        "mac": "11:22:33:44:55:66",
        "host": "my-laptop",
        "status": "C",
    },
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.thomson.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_get_thomson_data() -> Generator[MagicMock]:
    """Mock Thomson data fetching."""
    mock_get_data = MagicMock(return_value=MOCK_DEVICES)
    with (
        patch(
            "homeassistant.components.thomson.coordinator.get_thomson_data",
            new=mock_get_data,
        ),
        patch(
            "homeassistant.components.thomson.config_flow.get_thomson_data",
            new=mock_get_data,
        ),
    ):
        yield mock_get_data
