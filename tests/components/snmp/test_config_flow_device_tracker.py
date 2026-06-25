"""Tests for the SNMP device tracker config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.snmp.const import CONF_BASEOID, DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry

MOCK_HOST = "192.168.1.1"
MOCK_BASEOID = "1.3.6.1.2.1.2.2.1.6"
MOCK_CONFIG = {CONF_HOST: MOCK_HOST, CONF_BASEOID: MOCK_BASEOID}


@pytest.fixture
def mock_setup_entry() -> AsyncMock:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.snmp.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


async def test_user_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test a successful user config flow for device tracker."""
    with patch(
        "homeassistant.components.snmp.config_flow.async_validate_snmp",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_HOST] == MOCK_HOST
        assert result["data"][CONF_BASEOID] == MOCK_BASEOID


async def test_user_flow_cannot_connect(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test the user flow shows an error when SNMP validation fails."""
    with patch(
        "homeassistant.components.snmp.config_flow.async_validate_snmp",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_import_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test importing SNMP device tracker config from YAML."""
    with patch(
        "homeassistant.components.snmp.config_flow.async_validate_snmp",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=MOCK_CONFIG
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_HOST] == MOCK_HOST


async def test_import_flow_cannot_connect(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test import aborts when SNMP host is unreachable."""
    with patch(
        "homeassistant.components.snmp.config_flow.async_validate_snmp",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=MOCK_CONFIG
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"


async def test_already_configured(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test that duplicate host+baseoid entries are rejected."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.snmp.config_flow.async_validate_snmp",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"
