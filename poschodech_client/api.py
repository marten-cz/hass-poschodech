from __future__ import annotations
from typing import Any, Optional, List, Dict
import asyncio
import aiohttp
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
import json

API_BASE = "https://api.poschodoch.sk"
LOGIN_PATH = "/api/Auth/login"
CHANGEUNIT_PATH = "/api/Auth/changeunit?portalId=108588"
DAILY_RANGE_PATH = "/api/Flat/MeterDailyReadings"
SESSION_TIMEOUT = 20

class PoschodechApi:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._token: Optional[str] = None
        self._lock = asyncio.Lock()

    async def _login(self) -> str:
        async with self._lock:
            if self._token:
                return self._token
            login_url = f"{API_BASE}{LOGIN_PATH}"
            payload = {"username": self._username, "password": self._password}
            async with self._session.post(login_url, json=payload, timeout=SESSION_TIMEOUT) as resp:
                if resp.status != 200:
                    txt = await resp.text()
                    raise RuntimeError(f"Login failed: HTTP {resp.status} {txt}")
                data = await resp.json()
                token = data.get("token") or data.get("auth_token") or data.get("jwt")
                if not token:
                    raise RuntimeError("Login response missing token")

            change_url = f"{API_BASE}{CHANGEUNIT_PATH}"
            headers = {"Authorization": f"Bearer {token}"}
            async with self._session.post(change_url, headers=headers, timeout=SESSION_TIMEOUT) as resp2:
                if resp2.status != 200:
                    txt2 = await resp2.text()
                    raise RuntimeError(f"changeunit failed: HTTP {resp2.status} {txt2}")
                # This call returns plain/text, resp2.json() will fail
                data2 = json.loads(await resp2.text())
                new_token = (
                    data2.get("token")
                    or data2.get("access_token")
                    or data2.get("jwt")
                    or data2.get("auth_token")
                )
                if not new_token:
                    raise RuntimeError("changeunit response missing new auth_token")
                self._token = new_token
                return new_token

    async def _authorized_get(self, path: str, params: Optional[Dict[str, str]] = None) -> Any:
        token = self._token or await self._login()
        url = f"{API_BASE}{path}"
        if params:
            url = f"{url}?{urlencode(params, doseq=True)}"
        headers = {"Authorization": f"Bearer {token}"}
        async with self._session.get(url, headers=headers, timeout=SESSION_TIMEOUT) as resp:
            if resp.status == 401:
                self._token = None
                token = await self._login()
                headers = {"Authorization": f"Bearer {token}"}
                async with self._session.get(url, headers=headers, timeout=SESSION_TIMEOUT) as resp2:
                    if resp2.status != 200:
                        txt2 = await resp2.text()
                        raise RuntimeError(f"Data fetch failed: HTTP {resp2.status} {txt2}")
                    return await resp2.json()
            if resp.status != 200:
                txt = await resp.text()
                raise RuntimeError(f"Data fetch failed: HTTP {resp.status} {txt}")
            return await resp.json()

    @staticmethod
    def _today_prague():
        return datetime.now(ZoneInfo("Europe/Prague")).date()

    async def fetch_latest_for_flat(self, flat_name: str) -> Any:
        today = self._today_prague()
        date_from = (today - timedelta(days=1)).isoformat()
        date_to = today.isoformat()
        params = {
            "menuId": "56",
            "dateFrom": date_from,
            "dateTo": date_to,
            "Search": flat_name,
        }
        return await self._authorized_get(DAILY_RANGE_PATH, params=params)

    @staticmethod
    def extract_records(data: Any) -> List[dict]:
        if not isinstance(data, dict):
            return []
        items = data.get("Consumption")
        if not isinstance(items, list):
            return []
        return [it for it in items if isinstance(it, dict)]

    @staticmethod
    def make_key(record: dict) -> str:
        apt = str(record.get("CisloBytu", "")).strip()
        typ = str(record.get("Type", "")).strip()
        num = str(record.get("MeterNumber", "")).strip()
        return f"poschodech_{apt}_{typ}_{num}"

    @staticmethod
    def parse_state_to(record: dict) -> Optional[float]:
        val = record.get("StateTo")
        if val is None:
            return None
        try:
            if isinstance(val, str):
                return float(val.replace(",", "."))
            return float(val)
        except Exception:
            return None

    @staticmethod
    def unit(record: dict) -> str:
        u = record.get("Unit")
        return "m³" if isinstance(u, str) and u.lower() == "m3" else (str(u) if u is not None else "")
