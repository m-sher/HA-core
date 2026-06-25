"""Config flow for the FortiOS integration."""

from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_TOKEN, CONF_VERIFY_SSL

from .const import DEFAULT_VERIFY_SSL, DOMAIN
from .coordinator import create_fortios_api, get_fortios_devices

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_TOKEN): str,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


def _validate_fortios_connection(
    host: str, token: str, verify_ssl: bool
) -> bool:
    """Login and fetch devices; return True if the API responds successfully."""
    fgt = create_fortios_api(host, token, verify_ssl)
    if fgt is None:
        return False
    try:
        get_fortios_devices(fgt)
    except Exception:  # noqa: BLE001
        return False
    return True


class FortiOSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FortiOS."""

    VERSION = 1

    async def _async_can_connect(self, user_input: dict[str, Any]) -> bool:
        """Return true if FortiOS accepts credentials and returns device data."""
        return await self.hass.async_add_executor_job(
            _validate_fortios_connection,
            user_input[CONF_HOST],
            user_input[CONF_TOKEN],
            user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
        )

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
