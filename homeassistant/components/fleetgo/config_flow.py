"""Config flow for the FleetGO integration."""

from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_INCLUDE,
    CONF_PASSWORD,
    CONF_USERNAME,
)

from .const import DOMAIN
from .coordinator import create_fleetgo_api

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Optional(CONF_INCLUDE, default=[]): vol.All([str]),
    }
)


class FleetGoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FleetGO."""

    VERSION = 1

    async def _async_can_connect(self, user_input: dict[str, Any]) -> bool:
        """Return true if FleetGO authenticates successfully."""
        api = await self.hass.async_add_executor_job(
            create_fleetgo_api,
            user_input[CONF_CLIENT_ID],
            user_input[CONF_CLIENT_SECRET],
            user_input[CONF_USERNAME],
            user_input[CONF_PASSWORD],
        )
        return api is not None

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_USERNAME: user_input[CONF_USERNAME]})
            if await self._async_can_connect(user_input):
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Import existing configuration from configuration.yaml."""
        self._async_abort_entries_match({CONF_USERNAME: import_data[CONF_USERNAME]})
        if await self._async_can_connect(import_data):
            return self.async_create_entry(
                title=import_data[CONF_USERNAME], data=import_data
            )
        return self.async_abort(reason="cannot_connect")
