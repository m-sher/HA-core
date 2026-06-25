"""Config flow for the Synology SRM integration."""

from typing import Any, override

import synology_srm
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.helpers import config_validation as cv

from .const import (
    DEFAULT_PORT,
    DEFAULT_SSL,
    DEFAULT_USERNAME,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)
from .coordinator import create_client, fetch_devices

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_SSL, default=DEFAULT_SSL): bool,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


def validate_connection(data: dict[str, Any]) -> None:
    """Validate that we can connect to the Synology SRM router."""
    client = create_client(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        https=data[CONF_SSL],
        verify_ssl=data[CONF_VERIFY_SSL],
    )
    fetch_devices(client)


class SynologySrmConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Synology SRM."""

    VERSION = 1

    async def _async_can_connect(self, user_input: dict[str, Any]) -> bool:
        """Return True if the router returns data."""
        try:
            await self.hass.async_add_executor_job(validate_connection, user_input)
        except synology_srm.http.SynologyException:
            return False
        return True

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
