"""Common fixtures for the FleetGO integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.fleetgo.const import DOMAIN
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_PASSWORD,
    CONF_USERNAME,
)

from tests.common import MockConfigEntry

MOCK_USERNAME = "user@example.com"
MOCK_PASSWORD = "password"
MOCK_CLIENT_ID = "client-id"
MOCK_CLIENT_SECRET = "client-secret"

MOCK_CONFIG = {
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_CLIENT_ID: MOCK_CLIENT_ID,
    CONF_CLIENT_SECRET: MOCK_CLIENT_SECRET,
}

MOCK_DEVICES = {
    "AB123CD": {
        "license_plate": "AB-123-CD",
        "latitude": 52.0,
        "longitude": 4.0,
        "make": "Toyota",
        "model": "Corolla",
    },
    "XY789ZW": {
        "license_plate": "XY-789-ZW",
        "latitude": 53.0,
        "longitude": 5.0,
        "make": "VW",
        "model": "Golf",
    },
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.fleetgo.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_USERNAME)


@pytest.fixture
def mock_fleetgo_api() -> Generator[MagicMock]:
    """Mock FleetGO API."""
    mock_api = MagicMock()
    with (
        patch(
            "homeassistant.components.fleetgo.coordinator.create_fleetgo_api",
            return_value=mock_api,
        ),
        patch(
            "homeassistant.components.fleetgo.config_flow.create_fleetgo_api",
            return_value=mock_api,
        ),
        patch(
            "homeassistant.components.fleetgo.coordinator.get_fleetgo_devices",
            return_value=MOCK_DEVICES,
        ),
    ):
        yield mock_api
