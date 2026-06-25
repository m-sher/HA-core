"""Config flow for the SNMP device tracker."""

from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST

from .const import (
    CONF_AUTH_KEY,
    CONF_BASEOID,
    CONF_COMMUNITY,
    CONF_PRIV_KEY,
    DEFAULT_COMMUNITY,
    DOMAIN,
)
from .coordinator import async_validate_snmp

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_BASEOID): str,
        vol.Optional(CONF_COMMUNITY, default=DEFAULT_COMMUNITY): str,
        vol.Optional(CONF_AUTH_KEY): str,
        vol.Optional(CONF_PRIV_KEY): str,
    }
)


class SnmpConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SNMP device tracker."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match(
                {CONF_HOST: user_input[CONF_HOST], CONF_BASEOID: user_input[CONF_BASEOID]}
            )
            if await async_validate_snmp(self.hass, user_input):
                return self.async_create_entry(
                    title=f"{user_input[CONF_HOST]} ({user_input[CONF_BASEOID]})",
                    data=user_input,
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Import existing configuration from configuration.yaml."""
        self._async_abort_entries_match(
            {CONF_HOST: import_data[CONF_HOST], CONF_BASEOID: import_data[CONF_BASEOID]}
        )
        if await async_validate_snmp(self.hass, import_data):
            return self.async_create_entry(
                title=f"{import_data[CONF_HOST]} ({import_data[CONF_BASEOID]})",
                data=import_data,
            )
        return self.async_abort(reason="cannot_connect")
