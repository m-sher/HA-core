"""Common fixtures for the BT Smart Hub integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.bt_smarthub.const import DOMAIN
from homeassistant.components.bt_smarthub.coordinator import BTSmartHubDevice
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.254"

MOCK_CONFIG = {CONF_HOST: MOCK_HOST}

MOCK_DEVICES = {
    "AA:BB:CC:DD:EE:FF": BTSmartHubDevice(
        mac="AA:BB:CC:DD:EE:FF",
        ip_address="192.168.1.10",
        host="my-phone",
        name="my-phone",
    ),
    "11:22:33:44:55:66": BTSmartHubDevice(
        mac="11:22:33:44:55:66",
        ip_address="192.168.1.11",
        host="my-laptop",
        name="my-laptop",
    ),
}

MOCK_RAW_DEVICES = [
    {
        "PhysAddress": "AA:BB:CC:DD:EE:FF",
        "IPAddress": "192.168.1.10",
        "UserHostName": "my-phone",
        "name": "my-phone",
        "Active": True,
    },
    {
        "PhysAddress": "11:22:33:44:55:66",
        "IPAddress": "192.168.1.11",
        "UserHostName": "my-laptop",
        "name": "my-laptop",
        "Active": True,
    },
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
def mock_btsmarthub() -> Generator[MagicMock]:
    """Mock BTSmartHub client."""
    with (
        patch(
            "homeassistant.components.bt_smarthub.coordinator.BTSmartHub"
        ) as mock_coord,
        patch(
            "homeassistant.components.bt_smarthub.config_flow.BTSmartHub", new=mock_coord
        ),
    ):
        instance = MagicMock()
        instance.get_devicelist.return_value = MOCK_RAW_DEVICES
        mock_coord.return_value = instance
        yield mock_coord
