"""Config and options flow for the Pegasus Astro Unity integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import PegasusUnityConfigEntry
from .api import (
    PegasusUnityApiError,
    PegasusUnityClient,
    PegasusUnityConnectionError,
)
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class PegasusUnityConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Pegasus Unity."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step where the user enters host and port."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            session = async_get_clientsession(self.hass)
            client = PegasusUnityClient(host, port, session)
            try:
                await client.get_server_version()
                await client.get_connected_devices()
            except (PegasusUnityConnectionError, PegasusUnityApiError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating Pegasus Unity server")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Pegasus Unity ({host})",
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: PegasusUnityConfigEntry,
    ) -> PegasusUnityOptionsFlow:
        """Return the options flow handler."""
        return PegasusUnityOptionsFlow()


class PegasusUnityOptionsFlow(OptionsFlow):
    """Handle the options flow (scan interval) for Pegasus Unity."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the scan interval option."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
