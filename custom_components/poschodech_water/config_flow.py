from __future__ import annotations
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_FLAT_NAME
from poschodech_client.api import PoschodechApi

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input.get(CONF_USERNAME)
            password = user_input.get(CONF_PASSWORD)
            flat_name = user_input.get(CONF_FLAT_NAME)

            try:
                session = async_get_clientsession(self.hass)
                api = PoschodechApi(session, username, password)
                data = await api.fetch_latest_for_flat(flat_name)
                if not isinstance(data, dict):
                    raise ValueError("unexpected_data")
                await self.async_set_unique_id(f"{username}:{flat_name}".lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=f"Poschodech ({flat_name})", data=user_input)
            except Exception:
                errors["base"] = "auth"

        data_schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_FLAT_NAME): str,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
