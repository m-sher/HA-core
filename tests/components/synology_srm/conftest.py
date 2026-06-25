"""Common fixtures for the Synology SRM integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.synology_srm.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.1"
MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "password",
    CONF_PORT: 8001,
    CONF_SSL: True,
    CONF_VERIFY_SSL: False,
}

MOCK_DEVICES = [
    {
        "mac": "AA:BB:CC:DD:EE:FF",
        "hostname": "my-phone",
        "ip_addr": "192.168.1.10",
        "is_online": True,
    },
    {
        "mac": "11:22:33:44:55:66",
        "hostname": "my-laptop",
        "ip_addr": "192.168.1.11",
        "is_online": True,
    },
]


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.synology_srm.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_synology_client() -> Generator[MagicMock]:
    """Mock the Synology SRM client."""
    with (
        patch(
            "homeassistant.components.synology_srm.coordinator.create_client"
        ) as mock_create,
        patch(
            "homeassistant.components.synology_srm.config_flow.create_client",
            new=mock_create,
        ),
        patch(
            "homeassistant.components.synology_srm.coordinator.fetch_devices",
            return_value=MOCK_DEVICES,
        ) as mock_fetch,
        patch(
            "homeassistant.components.synology_srm.config_flow.fetch_devices",
            new=mock_fetch,
        ),
    ):
        mock_create.return_value = MagicMock()
        yield mock_fetch
