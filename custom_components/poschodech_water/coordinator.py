from __future__ import annotations
from datetime import timedelta
import logging
from typing import Any
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from poschodech_client.api import PoschodechApi

_LOGGER = logging.getLogger(__name__)

class PoschodechCoordinator(DataUpdateCoordinator[list[dict]]):
    def __init__(self, hass: HomeAssistant, api: PoschodechApi, flat_name: str) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Poschodech Water Coordinator",
            update_interval=timedelta(hours=1),
        )
        self.api = api
        self.flat = flat_name

    async def _async_update_data(self) -> list[dict]:
        data = await self.api.fetch_latest_for_flat(self.flat)
        return self.api.extract_records(data)
