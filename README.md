# Poschodech Water (HACS)

Custom integration that logs in to `api.poschodech.sk`, switches unit via `/api/Auth/changeunit?portalId=108588`,
and fetches daily water consumption for your flat. It creates two sensors (Cold & Hot).

It also includes a standalone client library (`poschodech_client`) and a probe script for testing without Home Assistant.

## Install via HACS
1. Add this repository as a custom repository in HACS (category: Integration).
2. Install **Poschodech Water**.
3. Restart Home Assistant.
4. Add the integration, enter your **username**, **password**, and **Flat name**.

## Entities
- `sensor.poschodech_cold_water_consumption`
- `sensor.poschodech_hot_water_consumption`

These represent daily **measurement** values for the current date.
