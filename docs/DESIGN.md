# Pegasus Astro Unity — Home Assistant integration design

Date: 2026-07-16

## Goal

A Home Assistant custom integration that polls metrics from a Pegasus Astro
Unity platform server (the REST API served by Pegasus' Unity software, e.g.
`http://<host>:32000`). First supported device: **Pocket PowerBox Advance
(PPBAdvance)** — read-only monitoring (power, dew heaters, environment).
Control entities (switches, dew power) and other Pegasus devices come later.

## Background / API findings

- Swagger spec: `GET /docs/peg/api.json` (OpenAPI 3.0.1, "PegasusAstro v1",
  ~1300 paths covering the whole Pegasus device line).
- All responses use an envelope: `{"status": "success", "code": 200,
  "message": "...", "data": ...}`.
- `GET /Server/ServerVersion` → `data: "3.0.162.1"` (good connectivity check).
- `GET /Server/DeviceManager/Connected` → list of connected devices:
  `{uniqueKey, name, fullName, deviceID, firmware, revision}`.
  - `name` is the driver type (e.g. `"PPBAdvance"`), `deviceID` is the stable
    hardware serial (e.g. `"PPBAAOEVCHA"`), `uniqueKey` is the driver↔device
    session key used as `DriverUniqueKey` query param on driver endpoints.
- `GET /Driver/PPBAdvance/Report?DriverUniqueKey=<key>` → aggregate report:
  voltage, current, quadCurrent, power, temperature, humidity, dewPoint,
  isOverCurrent, averageAmps, ampsPerHour, wattPerHour, upTime (".NET
  TimeSpan" string), dewHubStatus (per-port power % + current + overcurrent),
  powerHubStatus / powerVariablePortStatus / ppbA_DualUSB2Status (ON/OFF).
- `GET /Driver/PPBAdvance/Dew/Auto` → auto-dew ON/OFF.
- `GET /Driver/PPBAdvance/Dew/Auto/Aggressiveness` → `{level: 1..10}`.
- `GET /Driver/PPBAdvance/Power/Variable` → nested JSON-string payload with
  the variable port voltage setting and switch state.

## Architecture

```
config entry (host, port)            options: scan interval (default 15 s)
        │
   PegasusUnityClient (api.py, aiohttp via HA shared session)
        │
   PegasusUnityCoordinator (DataUpdateCoordinator)
        │  per cycle: Connected → per PPBA: Report, Dew/Auto,
        │  Aggressiveness, Power/Variable  → {deviceID: PpbaData}
        ├── sensor.py          (per-device sensors via EntityDescription)
        └── binary_sensor.py   (status/problem binary sensors)
```

- One config entry per Unity server; every connected supported device becomes
  an HA device. Devices are keyed by `deviceID` (stable across restarts);
  `uniqueKey` is re-read from the Connected list every poll.
- A device absent from the Connected list → its entities become unavailable;
  the coordinator itself still succeeds.
- Server unreachable → `UpdateFailed` → all entities unavailable.
- Domain: `pegasus_unity`, iot_class `local_polling`, no external
  requirements (aiohttp from HA core).

## Entities (PPB Advance)

Sensors: input voltage (V), current (A), quad port current (A), power (W),
temperature (°C), humidity (%), dew point (°C), average current (A, diag),
amp hours (Ah, total_increasing, diag), energy (Wh, total_increasing),
uptime (s, duration, diag), auto-dew aggressiveness (diag),
variable port voltage (V, diag), dew heater 1/2 power (%),
dew heater 1/2 current (A).

Binary sensors: over current (problem), dew heater 1/2 over current
(problem, diag), quad 12V output (power), variable output (power),
USB2 hub (power), auto dew (running).

## Repo layout

HACS-compatible: `custom_components/pegasus_unity/` + `hacs.json`, GPL-3.0
LICENSE, README, GitHub Actions running hassfest + HACS validation.

## Testing

Validated against a live PPB Advance (firmware 2.12.3) behind Unity server
3.0.162.1 on HA 2025.12.3.
