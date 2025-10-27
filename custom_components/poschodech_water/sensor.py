from __future__ import annotations
from typing import Any, Dict, List
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .coordinator import PoschodechCoordinator
from poschodech_client.api import PoschodechApi

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: PoschodechCoordinator = data["coordinator"]

    entities: List[PoschodechRecordSensor] = []
    for rec in coordinator.data or []:
        key = PoschodechApi.make_key(rec)
        entities.append(PoschodechRecordSensor(coordinator, key))
    async_add_entities(entities)

class PoschodechRecordSensor(CoordinatorEntity[PoschodechCoordinator], SensorEntity):
    _attr_state_class = "total_increasing"

    def __init__(self, coordinator: PoschodechCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = key
        self._attr_name = key.replace("poschodech_", "Poschodech ").replace("_", " ")

    def _find_record(self) -> Dict[str, Any] | None:
        for rec in self.coordinator.data or []:
            if PoschodechApi.make_key(rec) == self._key:
                return rec
        return None

    @property
    def native_value(self) -> Any:
        rec = self._find_record()
        if not rec:
            return None
        return PoschodechApi.parse_state_to(rec)

    @property
    def native_unit_of_measurement(self) -> str | None:
        rec = self._find_record()
        if not rec:
            return None
        return PoschodechApi.unit(rec)

    @property
    def device_class(self) -> str | None:
        rec = self._find_record()
        if not rec:
            return None
        unit = (rec.get("Unit") or "").lower()
        typ = (rec.get("Type") or "").upper()
        if "m3" in unit and typ in ("S", "T"):
            return "water"
        return None

    @property
    def extra_state_attributes(self) -> dict:
        rec = self._find_record() or {}
        return {
            "CisloBytu": rec.get("CisloBytu"),
            "Apartment": rec.get("Apartment"),
            "Type": rec.get("Type"),
            "MeterNumber": rec.get("MeterNumber"),
            "DateFrom": rec.get("DateFrom"),
            "DateTo": rec.get("DateTo"),
            "StateFrom": rec.get("StateFrom"),
            "StateTo": rec.get("StateTo"),
            "Unit": rec.get("Unit"),
            "Consumption": rec.get("Consumption"),
        }
