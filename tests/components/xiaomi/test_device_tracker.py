"""The tests for the Xiaomi router device tracker platform."""

from unittest.mock import MagicMock, patch

import pytest

from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER_DOMAIN
from homeassistant.components.xiaomi.const import DOMAIN
from homeassistant.components.xiaomi.device_tracker import PLATFORM_SCHEMA
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PLATFORM, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.0.1"
MOCK_CONFIG = {
    CONF_HOST: MOCK_HOST,
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "passwordTest",
}


@pytest.fixture
def mock_get_token() -> MagicMock:
    """Mock get_token for successful auth."""
    with (
        patch(
            "homeassistant.components.xiaomi.coordinator.get_token",
            return_value="ef5860",
        ) as mock_token,
        patch(
            "homeassistant.components.xiaomi.config_flow.get_token",
            return_value="ef5860",
        ),
        patch(
            "homeassistant.components.xiaomi.coordinator.retrieve_list",
            return_value=[
                {
                    "mac": "23:83:BF:F6:38:A0",
                    "online": 1,
                    "name": "Device1",
                    "ip": [{"ip": "192.168.0.25"}],
                },
                {
                    "mac": "1D:98:EC:5E:D5:A6",
                    "online": 1,
                    "name": "Device2",
                    "ip": [{"ip": "192.168.0.3"}],
                },
            ],
        ),
    ):
        yield mock_token


async def test_platform_schema() -> None:
    """Testing minimal configuration schema."""
    config = PLATFORM_SCHEMA(
        {
            CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
            CONF_HOST: "192.168.0.1",
            CONF_PASSWORD: "passwordTest",
        }
    )
    assert config["username"] == "admin"
    assert config["password"] == "passwordTest"
    assert config["host"] == "192.168.0.1"


async def test_platform_schema_full() -> None:
    """Testing full configuration schema."""
    config = PLATFORM_SCHEMA(
        {
            CONF_PLATFORM: DEVICE_TRACKER_DOMAIN,
            CONF_HOST: "192.168.0.1",
            CONF_USERNAME: "alternativeAdminName",
            CONF_PASSWORD: "passwordTest",
        }
    )
    assert config["username"] == "alternativeAdminName"
    assert config["password"] == "passwordTest"
    assert config["host"] == "192.168.0.1"


async def test_legacy_platform_imports_config_entry(
    hass: HomeAssistant, mock_get_token: MagicMock
) -> None:
    """Test the legacy device_tracker platform imports a config entry."""
    with patch(
        "homeassistant.components.xiaomi.async_setup_entry", return_value=True
    ):
        assert await async_setup_component(
            hass,
            "device_tracker",
            {
                "device_tracker": [
                    {
                        "platform": DOMAIN,
                        CONF_HOST: MOCK_HOST,
                        CONF_PASSWORD: "passwordTest",
                    }
                ]
            },
        )
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].data[CONF_HOST] == MOCK_HOST
    assert entries[0].source == SOURCE_IMPORT


async def test_entities_created(
    hass: HomeAssistant, mock_get_token: MagicMock
) -> None:
    """Test device tracker entities are created from the coordinator data."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_HOST)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("device_tracker.device1") is not None
    assert hass.states.get("device_tracker.device2") is not None
