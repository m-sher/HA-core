"""Config flow for the BT Smart Hub integration."""

from typing import Any, override

from btsmarthub_devicelist import BTSmartHub
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST

from .const import CONF_SMARTHUB_MODEL, DEFAULT_HOST, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Optional(CONF_SMARTHUB_MODEL): vol.In([1, 2]),
    }
)


def _can_connect(host: str, smarthub_model: int | None) -> bool:
    """Return True if the BT Smart Hub returns device data."""
    client = BTSmartHub(router_ip=host, smarthub_model=smarthub_model)
    data = client.get_devicelist(only_active_devices=True)
    return data is not None


class BTSmartHubConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BT Smart Hub."""

    VERSION = 1

    async def _async_can_connect(self, user_input: dict[str, Any]) -> bool:
        """Return True if the hub returns data."""
        return await self.hass.async_add_executor_job(
            _can_connect,
            user_input[CONF_HOST],
            user_input.get(CONF_SMARTHUB_MODEL),
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
