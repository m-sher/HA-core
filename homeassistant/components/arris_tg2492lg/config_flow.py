"""Config flow for the Arris TG2492LG integration."""

from typing import Any, override

from aiohttp.client_exceptions import ClientResponseError
from arris_tg2492lg import ConnectBox
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_HOST, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ArrisTg2492lgConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Arris TG2492LG."""

    VERSION = 1

    async def _async_can_connect(self, user_input: dict[str, Any]) -> bool:
        """Return True if the Arris TG2492LG at host returns data."""
        url = f"http://{user_input[CONF_HOST]}"
        connect_box = ConnectBox(
            async_get_clientsession(self.hass), url, user_input[CONF_PASSWORD]
        )
        try:
            await connect_box.async_login()
        except ClientResponseError:
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
