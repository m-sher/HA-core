"""Config flow for the Aruba ClearPass integration."""

from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_CLIENT_ID, CONF_HOST

from .const import DOMAIN
from .coordinator import create_cppm_client

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_API_KEY): str,
    }
)


class CPPMConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aruba ClearPass."""

    VERSION = 1

    async def _async_can_connect(self, user_input: dict[str, Any]) -> bool:
        """Return true if ClearPass authenticates successfully."""
        cppm = await self.hass.async_add_executor_job(
            create_cppm_client,
            user_input[CONF_HOST],
            user_input[CONF_CLIENT_ID],
            user_input[CONF_API_KEY],
        )
        return cppm is not None

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
            if await self._async_can_connect(user_input):
                return self.async_create_entry(
                    title=user_input[CONF_HOST], data=user_input
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Import existing configuration from configuration.yaml."""
        self._async_abort_entries_match({CONF_HOST: import_data[CONF_HOST]})
        if await self._async_can_connect(import_data):
            return self.async_create_entry(
                title=import_data[CONF_HOST], data=import_data
            )
        return self.async_abort(reason="cannot_connect")
