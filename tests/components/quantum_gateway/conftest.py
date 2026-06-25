"""Common fixtures for the Quantum Gateway integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.quantum_gateway.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SSL

from tests.common import MockConfigEntry

MOCK_HOST = "myfiosgateway.com"
MOCK_PASSWORD = "password"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_SSL: True,
}

MOCK_DEVICES = {
    "FF:FF:FF:FF:FF:FE": "desktop",
    "FF:FF:FF:FF:FF:FF": "",
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.quantum_gateway.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_get_quantum_gateway_data() -> Generator[MagicMock]:
    """Mock Quantum Gateway data fetching."""
    mock_get_data = MagicMock(return_value=MOCK_DEVICES)
    with (
        patch(
            "homeassistant.components.quantum_gateway.coordinator.get_quantum_gateway_data",
            new=mock_get_data,
        ),
        patch(
            "homeassistant.components.quantum_gateway.config_flow.get_quantum_gateway_data",
            new=mock_get_data,
        ),
    ):
        yield mock_get_data
