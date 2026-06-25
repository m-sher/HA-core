"""Common fixtures for the Tomato integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.tomato.const import CONF_HTTP_ID, DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SSL, CONF_USERNAME

from tests.common import MockConfigEntry

MOCK_HOST = "tomato-router"
MOCK_USERNAME = "admin"
MOCK_PASSWORD = "password"
MOCK_HTTP_ID = "1234567890"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_HTTP_ID: MOCK_HTTP_ID,
    CONF_SSL: False,
}

MOCK_DEVICES = {
    "F4:F5:D8:AA:AA:AA": {"mac": "F4:F5:D8:AA:AA:AA", "name": "chromecast"},
    "58:EF:68:00:00:00": {"mac": "58:EF:68:00:00:00", "name": "wemo"},
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.tomato.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_get_tomato_data() -> Generator[MagicMock]:
    """Mock Tomato data fetching."""
    mock_get_data = MagicMock(return_value=MOCK_DEVICES)
    with (
        patch(
            "homeassistant.components.tomato.coordinator.get_tomato_data",
            new=mock_get_data,
        ),
        patch(
            "homeassistant.components.tomato.config_flow.get_tomato_data",
            new=mock_get_data,
        ),
    ):
        yield mock_get_data
