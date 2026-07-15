"""Data update coordinator for the Pegasus Astro Unity integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    PegasusUnityApiError,
    PegasusUnityClient,
    PegasusUnityConnectionError,
)
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, DRIVER_PPBADVANCE
from .parser import PpbaData, build_ppba_data

_LOGGER = logging.getLogger(__name__)


class PegasusUnityCoordinator(DataUpdateCoordinator[dict[str, PpbaData]]):
    """Polls the Unity server and builds per-device :class:`PpbaData`."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: PegasusUnityClient,
    ) -> None:
        """Initialise the coordinator with the poll interval from options."""
        interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.client = client
        self._known_device_ids: set[str] = set()

    async def _async_update_data(self) -> dict[str, PpbaData]:
        """Fetch and parse the state of every connected PPBAdvance device."""
        try:
            devices = await self.client.get_connected_devices()
        except (PegasusUnityConnectionError, PegasusUnityApiError) as err:
            raise UpdateFailed(f"Error fetching connected devices: {err}") from err

        result: dict[str, PpbaData] = {}
        for device in devices:
            if device.get("name") != DRIVER_PPBADVANCE:
                continue
            unique_key = device.get("uniqueKey")
            if not unique_key:
                _LOGGER.debug("Skipping device without uniqueKey: %s", device)
                continue

            try:
                report = await self.client.get_ppba_report(unique_key)
            except (PegasusUnityConnectionError, PegasusUnityApiError) as err:
                _LOGGER.warning(
                    "Failed to fetch report for %s: %s",
                    device.get("deviceID", unique_key),
                    err,
                )
                continue

            dew_auto = await self._fetch_optional(
                self.client.get_ppba_dew_auto, unique_key, "dew auto"
            )
            aggressiveness = await self._fetch_optional(
                self.client.get_ppba_dew_aggressiveness, unique_key, "aggressiveness"
            )
            power_variable = await self._fetch_optional(
                self.client.get_ppba_power_variable, unique_key, "power variable"
            )

            data = build_ppba_data(
                device, report, dew_auto, aggressiveness, power_variable
            )
            result[data.device_id] = data
            self._known_device_ids.add(data.device_id)

        missing = self._known_device_ids - set(result)
        for device_id in missing:
            _LOGGER.debug("Known device %s not present this cycle", device_id)

        return result

    async def _fetch_optional(self, method, unique_key: str, label: str):
        """Call an auxiliary endpoint, returning ``None`` (logged) on failure."""
        try:
            return await method(unique_key)
        except (PegasusUnityConnectionError, PegasusUnityApiError) as err:
            _LOGGER.debug("Optional '%s' fetch failed: %s", label, err)
            return None
