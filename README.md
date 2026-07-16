[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/avleen/ha-pegasus-unity?style=flat-square)](https://github.com/avleen/ha-pegasus-unity/releases/latest)
[![Validate](https://github.com/avleen/ha-pegasus-unity/actions/workflows/validate.yml/badge.svg)](https://github.com/avleen/ha-pegasus-unity/actions/workflows/validate.yml)

# Pegasus Astro Unity

A Home Assistant integration for monitoring Pegasus Astro observatory devices via the Pegasus Unity platform server.

**Disclaimer:** This integration is not affiliated with or endorsed by Pegasus Astro.

## About

This is a local-polling integration for the Pegasus Astro Unity platform server — the REST API exposed by Pegasus' Unity software running on the computer that the Pegasus devices are plugged into. The integration discovers connected devices from the Unity server and creates Home Assistant devices and entities for them.

## Currently Supported Devices

- **Pocket PowerBox Advance (PPBA)** — Read-only monitoring of power outputs, environmental sensors, dew heater status, and system health.

## Roadmap

Future versions will add:
- Control entities (power outputs, dew heater power, auto-dew settings)
- Support for additional Pegasus devices (UPBv3, DewMaster2, SaddlePowerBox, etc.)

Contributions are welcome!

## Requirements

- **Home Assistant 2025.12 or newer**
- A running Pegasus Unity server reachable from Home Assistant over the network
  - Tested with Unity 3.x (server version 3.0.162.1, PPBA firmware 2.12.3)

## Installation

### Via HACS (Recommended)

1. In Home Assistant, open **HACS**, then the overflow menu (⋮) → **Custom repositories**
2. Add this repository URL: `https://github.com/avleen/ha-pegasus-unity`
3. Select type: **Integration** and click **Add**
4. Search for **"Pegasus Astro Unity"** in HACS and download it
5. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/pegasus_unity` directory from this repository into your Home Assistant configuration folder's `custom_components/` directory
2. Restart Home Assistant

## Configuration

After installation:

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for and select **"Pegasus Astro Unity"**
3. Enter the host (IP address or hostname) and port (default: 32000) of your Pegasus Unity server
4. Optionally configure the polling interval (default: 15 seconds, range: 5–300 seconds)

## Entities

### Pocket PowerBox Advance (PPBA)

#### Sensors

| Entity | Unit | Notes |
|--------|------|-------|
| Voltage | V | System voltage |
| Current | A | Total current draw |
| Quad port current | A | Current on quad 12V output |
| Power | W | Current power consumption |
| Temperature | °C | Internal temperature |
| Humidity | % | Internal humidity |
| Dew point | °C | Calculated dew point |
| Average current | A | (Diagnostic) Average over time period |
| Amp hours | Ah | (Diagnostic) Total Ah consumed |
| Energy | Wh | Total Wh consumed |
| Uptime | s | (Diagnostic) Seconds since power on |
| Auto-dew aggressiveness | — | (Diagnostic) Auto-dew aggressiveness level (1–10) |
| Variable port voltage | V | (Diagnostic) Voltage on variable output |
| Dew heater 1 power | % | Dew heater 1 power level |
| Dew heater 2 power | % | Dew heater 2 power level |
| Dew heater 1 current | A | Dew heater 1 current draw |
| Dew heater 2 current | A | Dew heater 2 current draw |

#### Binary Sensors

| Entity | States | Notes |
|--------|--------|-------|
| Over current | On/Off | (Problem) System over-current condition |
| Quad 12V output | On/Off | Quad output state |
| Variable output | On/Off | Variable output state |
| USB2 hub | On/Off | USB2 hub state |
| Auto dew | On/Off | Auto-dew enabled/disabled |
| Dew heater 1 over current | On/Off | (Problem, Diagnostic) Dew heater 1 over-current |
| Dew heater 2 over current | On/Off | (Problem, Diagnostic) Dew heater 2 over-current |

## How It Works

The integration periodically polls the Pegasus Unity server REST API to:

1. Discover connected devices via `/Server/DeviceManager/Connected`
2. Fetch device-specific data (e.g., `/Driver/PPBAdvance/Report` for PPBA devices)
3. Create or update Home Assistant entities based on the device data

Entity IDs are keyed by the device hardware serial number, so they persist across Unity server restarts.

## Development

Design notes and technical details are in [`docs/DESIGN.md`](docs/DESIGN.md).

This integration is licensed under the GNU General Public License v3.0. See [`LICENSE`](LICENSE) for details.

Pull requests and contributions are welcome!
