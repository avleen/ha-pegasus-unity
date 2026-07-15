"""The Pegasus Astro Unity integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PegasusUnityClient
from .coordinator import PegasusUnityCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

type PegasusUnityConfigEntry = ConfigEntry[PegasusUnityCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: PegasusUnityConfigEntry
) -> bool:
    """Set up Pegasus Unity from a config entry."""
    session = async_get_clientsession(hass)
    client = PegasusUnityClient(
        entry.data[CONF_HOST], entry.data[CONF_PORT], session
    )
    coordinator = PegasusUnityCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: PegasusUnityConfigEntry
) -> None:
    """Reload the entry when its options change (e.g. scan interval)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: PegasusUnityConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
