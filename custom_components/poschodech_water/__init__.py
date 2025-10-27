# custom_components/poschodech_water/__init__.py
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS, CONF_USERNAME, CONF_PASSWORD, CONF_FLAT_NAME
from poschodech_client.api import PoschodechApi
from .coordinator import PoschodechCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Poschodech Water integration from a config entry."""

    session = async_get_clientsession(hass)
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    # Prefer flat_name and update interval from options if available
    flat_name = entry.options.get(CONF_FLAT_NAME, entry.data[CONF_FLAT_NAME])
    interval_hours = entry.options.get("update_interval_hours", 1)
    update_interval = timedelta(hours=interval_hours)

    api = PoschodechApi(session, username, password)
    coordinator = PoschodechCoordinator(
        hass=hass,
        api=api,
        flat_name=flat_name,
        update_interval=update_interval,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "flat_name": flat_name,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _handle_refresh(call):
        """Manually trigger a refresh via service."""
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "refresh", _handle_refresh)

    _LOGGER.info("Poschodech Water integration initialized (flat=%s, interval=%sh)", flat_name, interval_hours)
    return True


# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Unload the integration when removed from Home Assistant."""
#     unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
#     if unload_ok:
#         hass.data[DOMAIN].pop(entry.entry_id, None)
#         _LOGGER.info("Poschodech Water integration unloaded: %s", entry.entry_id)
#     return unload_ok
