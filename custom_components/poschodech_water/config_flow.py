# custom_components/poschodech_water/config_flow.py
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_FLAT_NAME,
)

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from poschodech_client.api import PoschodechApi


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Poschodech Water."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            # Persist options
            return self.async_create_entry(title="", data=user_input)

        # Defaults: pull from options first, fall back to data
        default_flat = self.config_entry.options.get(
            CONF_FLAT_NAME, self.config_entry.data.get(CONF_FLAT_NAME, "")
        )
        default_interval = self.config_entry.options.get("update_interval_hours", 1)

        schema = vol.Schema(
            {
                vol.Required(CONF_FLAT_NAME, default=default_flat): str,
                vol.Required("update_interval_hours", default=default_interval): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow to add Poschodech Water via UI (no YAML)."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input.get(CONF_USERNAME, "")
            password = user_input.get(CONF_PASSWORD, "")
            flat_name = user_input.get(CONF_FLAT_NAME, "")

            # Validate credentials + flat by calling the API once.
            try:
                session = async_get_clientsession(self.hass)
                api = PoschodechApi(session, username, password)
                data = await api.fetch_latest_for_flat(flat_name)
                if not isinstance(data, dict):
                    raise ValueError("unexpected_data")

                # Use username + flat_name as unique id to prevent duplicates
                await self.async_set_unique_id(f"{username}:{flat_name}".lower())
                self._abort_if_unique_id_configured()

                # Store creds in data; options can override flat_name & interval later
                return self.async_create_entry(
                    title=f"Poschodech ({flat_name})",
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_FLAT_NAME: flat_name,
                    },
                )
            except Exception:
                errors["base"] = "auth"

        # Initial form schema
        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_FLAT_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlowHandler:
        return OptionsFlowHandler(config_entry)
