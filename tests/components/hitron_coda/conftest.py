"""Common fixtures for the Hitron CODA integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.hitron_coda.const import DEFAULT_TYPE, DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_TYPE, CONF_USERNAME

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.0.1"
MOCK_USERNAME = "cusadmin"
MOCK_PASSWORD = "password"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_TYPE: DEFAULT_TYPE,
}

MOCK_DEVICES = {
    "AA:BB:CC:DD:EE:FF": "my-phone",
    "11:22:33:44:55:66": "my-laptop",
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.hitron_coda.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_get_hitron_coda_data() -> Generator[MagicMock]:
    """Mock Hitron CODA data fetching."""
    mock_get_data = MagicMock(return_value=MOCK_DEVICES)
    with (
        patch(
            "homeassistant.components.hitron_coda.coordinator.get_hitron_coda_data",
            new=mock_get_data,
        ),
        patch(
            "homeassistant.components.hitron_coda.config_flow.get_hitron_coda_data",
            new=mock_get_data,
        ),
    ):
        yield mock_get_data
