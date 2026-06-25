"""Common fixtures for the BT Smart Hub integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.bt_smarthub.const import DOMAIN, Device
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.254"

MOCK_CONFIG = {CONF_HOST: MOCK_HOST}

MOCK_DEVICES = [
    Device("192.168.1.10", "AA:BB:CC:DD:EE:FF", "my-phone", True, "my-phone"),
    Device("192.168.1.11", "11:22:33:44:55:66", "my-laptop", True, "my-laptop"),
]


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.bt_smarthub.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_get_bt_smarthub_data() -> Generator[MagicMock]:
    """Mock BT Smart Hub data fetching."""
    mock_get_data = MagicMock(return_value=MOCK_DEVICES)
    with (
        patch(
            "homeassistant.components.bt_smarthub.coordinator.get_bt_smarthub_data",
            new=mock_get_data,
        ),
        patch(
            "homeassistant.components.bt_smarthub.config_flow.get_bt_smarthub_data",
            new=mock_get_data,
        ),
    ):
        yield mock_get_data
