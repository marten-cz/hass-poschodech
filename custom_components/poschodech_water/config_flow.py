# custom_components/poschodech_water/config_flow.py
from __future__ import annotations
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_FLAT_NAME

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            # Optionally, validate credentials here (e.g., try logging in).
            # If OK:
            return self.async_create_entry(
                title=user_input[CONF_FLAT_NAME],
                data={
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_FLAT_NAME: user_input[CONF_FLAT_NAME],
                },
            )

        data_schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_FLAT_NAME): str,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

# (Optional) Options flow if you need editable options later.
