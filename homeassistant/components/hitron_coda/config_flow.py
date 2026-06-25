"""Config flow for the Hitron CODA integration."""

from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_TYPE, CONF_USERNAME

from .const import DEFAULT_TYPE, DOMAIN
from .coordinator import get_hitron_coda_data

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_TYPE, default=DEFAULT_TYPE): str,
    }
)


class HitronCodaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hitron CODA."""

    VERSION = 1

    async def _async_can_connect(self, user_input: dict[str, Any]) -> bool:
        """Return true if the Hitron CODA router returns data."""
        devices = await self.hass.async_add_executor_job(
            get_hitron_coda_data,
            user_input[CONF_HOST],
            user_input[CONF_USERNAME],
            user_input[CONF_PASSWORD],
            user_input.get(CONF_TYPE, DEFAULT_TYPE),
        )
        return devices is not None

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
