"""Pure parsing helpers for the Pegasus Astro Unity integration.

This module deliberately avoids importing Home Assistant so that the parsing
logic can be exercised standalone (e.g. against a live server) and unit tested
without a full HA install. It turns the raw JSON payloads returned by the Unity
REST API into frozen dataclasses consumed by the coordinator and entities.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

# .NET TimeSpan: "[-][d.]hh:mm:ss[.fffffff]".
_TIMESPAN_RE = re.compile(
    r"^(?:(?P<days>\d+)\.)?(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})(?:\.(?P<frac>\d+))?$"
)


@dataclass(frozen=True)
class DewPortData:
    """State of a single dew heater port."""

    number: int
    power_pct: int | None
    current: float | None
    is_over_current: bool | None


@dataclass(frozen=True)
class PpbaData:
    """Parsed snapshot of a Pocket PowerBox Advance device."""

    unique_key: str
    device_id: str
    full_name: str
    firmware: str

    # Core readings from the aggregate report.
    voltage: float | None
    current: float | None
    quad_current: float | None
    power: float | None
    temperature: float | None
    humidity: float | None
    dew_point: float | None
    is_over_current: bool | None
    average_amps: float | None
    amp_hours: float | None
    watt_hours: float | None
    uptime_seconds: int | None

    # Dew heater ports.
    dew_ports: list[DewPortData]

    # Switch states from the aggregate report.
    power_hub_on: bool | None
    variable_port_on: bool | None
    dual_usb2_on: bool | None

    # Auxiliary readings (may be None if their endpoints failed).
    auto_dew_on: bool | None
    aggressiveness: int | None
    variable_voltage: int | None


def parse_timespan(value: str | None) -> int | None:
    """Parse a .NET TimeSpan string into whole seconds.

    Tolerates an optional leading days component and an optional fractional
    seconds part. Returns ``None`` for missing or unparseable input.
    """
    if not value:
        return None
    match = _TIMESPAN_RE.match(value.strip())
    if match is None:
        _LOGGER.debug("Unparseable TimeSpan value: %r", value)
        return None
    days = int(match.group("days") or 0)
    hours = int(match.group("h"))
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def _switch_on(message: dict | None) -> bool | None:
    """Return True/False from a ``{"state": "ON"|"OFF"}`` style block."""
    if not isinstance(message, dict):
        return None
    state = message.get("state")
    if state is None:
        return None
    return str(state).upper() == "ON"


def _parse_dew_ports(dew_hub_status: dict | None) -> list[DewPortData]:
    """Extract the list of dew heater ports from ``dewHubStatus``."""
    ports: list[DewPortData] = []
    if not isinstance(dew_hub_status, dict):
        return ports
    for entry in dew_hub_status.get("hub", []) or []:
        if not isinstance(entry, dict):
            continue
        port = entry.get("port") or {}
        current = entry.get("current") or {}
        number = port.get("number")
        if number is None:
            continue
        ports.append(
            DewPortData(
                number=int(number),
                power_pct=(
                    int(port["power"]) if port.get("power") is not None else None
                ),
                current=(
                    float(current["value"])
                    if current.get("value") is not None
                    else None
                ),
                is_over_current=current.get("isOverCurrent"),
            )
        )
    return ports


def _parse_variable_voltage(power_variable_message: dict | None) -> int | None:
    """Extract the variable power port voltage from the aggregate driver blob.

    The ``root`` values are JSON-encoded strings that must be decoded first.
    """
    if not isinstance(power_variable_message, dict):
        return None
    root = power_variable_message.get("root")
    if not isinstance(root, dict):
        return None
    raw_state = root.get("PowerVariablePortState")
    if not raw_state:
        return None
    try:
        state = json.loads(raw_state)
    except (json.JSONDecodeError, TypeError) as err:
        _LOGGER.debug("Unable to decode PowerVariablePortState: %s", err)
        return None
    voltage = state.get("Voltage")
    if voltage is None:
        return None
    return int(voltage)


def build_ppba_data(
    device: dict,
    report_message: dict,
    dew_auto_message: dict | None,
    aggressiveness_message: dict | None,
    power_variable_message: dict | None,
) -> PpbaData:
    """Build a :class:`PpbaData` from raw API message payloads.

    ``device`` is an entry from ``/Server/DeviceManager/Connected``. The
    ``*_message`` arguments are the unwrapped ``data.message`` blobs from the
    respective driver endpoints; the auxiliary ones may be ``None`` if their
    endpoint failed.
    """
    return PpbaData(
        unique_key=device.get("uniqueKey", ""),
        device_id=device.get("deviceID", ""),
        full_name=device.get("fullName", device.get("name", "PPBAdvance")),
        firmware=device.get("firmware", ""),
        voltage=report_message.get("voltage"),
        current=report_message.get("current"),
        quad_current=report_message.get("quadCurrent"),
        power=report_message.get("power"),
        temperature=report_message.get("temperature"),
        humidity=report_message.get("humidity"),
        dew_point=report_message.get("dewPoint"),
        is_over_current=report_message.get("isOverCurrent"),
        average_amps=report_message.get("averageAmps"),
        amp_hours=report_message.get("ampsPerHour"),
        watt_hours=report_message.get("wattPerHour"),
        uptime_seconds=parse_timespan(report_message.get("upTime")),
        dew_ports=_parse_dew_ports(report_message.get("dewHubStatus")),
        power_hub_on=_switch_on(report_message.get("powerHubStatus")),
        variable_port_on=_switch_on(report_message.get("powerVariablePortStatus")),
        dual_usb2_on=_switch_on(report_message.get("ppbA_DualUSB2Status")),
        auto_dew_on=(
            _switch_on(dew_auto_message.get("switch"))
            if isinstance(dew_auto_message, dict)
            else None
        ),
        aggressiveness=(
            aggressiveness_message.get("level")
            if isinstance(aggressiveness_message, dict)
            else None
        ),
        variable_voltage=_parse_variable_voltage(power_variable_message),
    )
