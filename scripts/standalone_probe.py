#!/usr/bin/env python3
import argparse
import asyncio
import aiohttp
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from poschodech_client.api import PoschodechApi

async def main():
    ap = argparse.ArgumentParser(description="Probe Poschodech daily readings (per-record sensors)")
    ap.add_argument("--username", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--flat-name", required=True, help="Flat name for Search parameter")
    args = ap.parse_args()

    async with aiohttp.ClientSession() as session:
        api = PoschodechApi(session, args.username, args.password)
        await api._login()
        data = await api.fetch_latest_for_flat(args.flat_name)
        records = api.extract_records(data)
        if not records:
            print("No records found. Check flat name or date range.")
            raise SystemExit(2)

        for rec in records:
            key = api.make_key(rec)
            val = api.parse_state_to(rec)
            unit = api.unit(rec)
            print(f"{key}: {val} {unit} (Apartment={rec.get('Apartment')}, Type={rec.get('Type')})")

if __name__ == "__main__":
    asyncio.run(main())
