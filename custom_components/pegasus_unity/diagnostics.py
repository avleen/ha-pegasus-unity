"""Diagnostics support for the Pegasus Astro Unity integration."""

from __future__ import annotations

import dataclasses
from typing import Any

from homeassistant.core import HomeAssistant

from . import PegasusUnityConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: PegasusUnityConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": {
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "coordinator_data": {
            device_id: dataclasses.asdict(data)
            for device_id, data in coordinator.data.items()
        },
    }
