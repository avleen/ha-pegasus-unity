"""Constants for the Pegasus Astro Unity integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "pegasus_unity"

# Default TCP port exposed by the Pegasus Astro Unity platform server.
DEFAULT_PORT: Final = 32000

# Polling interval, in seconds, used when the user has not overridden it.
DEFAULT_SCAN_INTERVAL: Final = 15

# Bounds for the user-configurable scan interval (seconds).
MIN_SCAN_INTERVAL: Final = 5
MAX_SCAN_INTERVAL: Final = 300

# Options key holding the poll interval.
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Manufacturer string reported for every Unity device.
MANUFACTURER: Final = "Pegasus Astro"

# Driver "name" reported by the server for the Pocket PowerBox Advance.
DRIVER_PPBADVANCE: Final = "PPBAdvance"
