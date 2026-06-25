"""Common fixtures for the ubus integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.ubus.const import CONF_DHCP_SOFTWARE, DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.1"
MOCK_USERNAME = "root"
MOCK_PASSWORD = "password"

MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: MOCK_USERNAME,
    CONF_PASSWORD: MOCK_PASSWORD,
    CONF_DHCP_SOFTWARE: "dnsmasq",
}


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ubus.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)


@pytest.fixture
def mock_validate_connection() -> Generator[AsyncMock]:
    """Mock ubus connection validation."""
    with patch(
        "homeassistant.components.ubus.config_flow.validate_connection",
        return_value=True,
    ) as mock_validate:
        yield mock_validate
