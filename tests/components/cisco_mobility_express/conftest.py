"""Common fixtures for the Cisco Mobility Express integration tests."""

from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.cisco_mobility_express.const import (
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.1"
MOCK_USERNAME = "admin"
MOCK_PASSWORD = "password"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_SSL: DEFAULT_SSL,
    CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
}

MOCK_DEVICES = {
    "AA:BB:CC:DD:EE:FF": {
        "macaddr": "AA:BB:CC:DD:EE:FF",
        "clId": "my-phone",
        "ssid": "HomeWiFi",
    },
    "11:22:33:44:55:66": {
        "macaddr": "11:22:33:44:55:66",
        "clId": "my-laptop",
        "ssid": "HomeWiFi",
    },
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.cisco_mobility_express.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_cisco_me() -> Generator[MagicMock]:
    """Mock Cisco Mobility Express controller."""
    controller = MagicMock()
    controller.is_logged_in.return_value = True
    controller.get_associated_devices.return_value = [
        SimpleNamespace(**device) for device in MOCK_DEVICES.values()
    ]

    with (
        patch(
            "homeassistant.components.cisco_mobility_express.coordinator.CiscoMobilityExpress",
            return_value=controller,
        ) as mock_cls,
        patch(
            "homeassistant.components.cisco_mobility_express.config_flow.get_cisco_me_controller",
            return_value=controller,
        ),
        patch(
            "homeassistant.components.cisco_mobility_express.coordinator.get_cisco_me_data",
            return_value=MOCK_DEVICES,
        ),
    ):
        yield mock_cls
