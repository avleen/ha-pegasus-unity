"""Async REST client for the Pegasus Astro Unity platform server.

This module is intentionally free of Home Assistant imports so that it remains a
clean, standalone client. The :class:`aiohttp.ClientSession` is injected by the
caller (Home Assistant provides a shared session via
``homeassistant.helpers.aiohttp_client.async_get_clientsession``).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10


class PegasusUnityError(Exception):
    """Base error for the Pegasus Unity client."""


class PegasusUnityConnectionError(PegasusUnityError):
    """Raised when the server cannot be reached (network/timeout errors)."""


class PegasusUnityApiError(PegasusUnityError):
    """Raised when the server returns an unexpected or unsuccessful envelope."""


class PegasusUnityClient:
    """Minimal async client for the Unity REST API."""

    def __init__(
        self, host: str, port: int, session: aiohttp.ClientSession
    ) -> None:
        """Store connection details and the injected aiohttp session."""
        self._host = host
        self._port = port
        self._session = session
        self._base_url = f"http://{host}:{port}"
        self._timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    async def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Perform a GET request and return the envelope's ``data`` payload.

        Raises :class:`PegasusUnityConnectionError` on network/timeout failures
        and :class:`PegasusUnityApiError` on a malformed or unsuccessful
        envelope.
        """
        url = f"{self._base_url}{path}"
        try:
            async with self._session.get(
                url, params=params, timeout=self._timeout
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise PegasusUnityConnectionError(
                f"Timeout connecting to {url}"
            ) from err
        except aiohttp.ClientError as err:
            raise PegasusUnityConnectionError(
                f"Error connecting to {url}: {err}"
            ) from err

        if not isinstance(payload, dict):
            raise PegasusUnityApiError(f"Unexpected response from {url}: {payload!r}")
        if payload.get("status") != "success" or payload.get("code") != 200:
            raise PegasusUnityApiError(
                f"Unsuccessful response from {url}: "
                f"status={payload.get('status')} code={payload.get('code')} "
                f"message={payload.get('message')}"
            )
        if "data" not in payload:
            raise PegasusUnityApiError(f"Response from {url} missing data field")
        return payload["data"]

    @staticmethod
    def _extract_message(data: Any) -> dict:
        """Return the ``message`` sub-object of a driver ``data`` payload."""
        if not isinstance(data, dict) or "message" not in data:
            raise PegasusUnityApiError(f"Driver response missing message: {data!r}")
        message = data["message"]
        if not isinstance(message, dict):
            raise PegasusUnityApiError(f"Driver message is not an object: {message!r}")
        return message

    async def get_server_version(self) -> str:
        """Return the server version string. Used for connectivity checks."""
        data = await self._request("/Server/ServerVersion")
        if not isinstance(data, str):
            raise PegasusUnityApiError(f"Unexpected server version payload: {data!r}")
        return data

    async def get_connected_devices(self) -> list[dict]:
        """Return the list of currently connected device descriptors."""
        data = await self._request("/Server/DeviceManager/Connected")
        if not isinstance(data, list):
            raise PegasusUnityApiError(f"Unexpected connected payload: {data!r}")
        return data

    async def get_ppba_report(self, unique_key: str) -> dict:
        """Return the aggregate readings report for a PPBAdvance device."""
        data = await self._request(
            "/Driver/PPBAdvance/Report", {"DriverUniqueKey": unique_key}
        )
        return self._extract_message(data)

    async def get_ppba_dew_auto(self, unique_key: str) -> dict:
        """Return the auto-dew switch state for a PPBAdvance device."""
        data = await self._request(
            "/Driver/PPBAdvance/Dew/Auto", {"DriverUniqueKey": unique_key}
        )
        return self._extract_message(data)

    async def get_ppba_dew_aggressiveness(self, unique_key: str) -> dict:
        """Return the auto-dew aggressiveness level for a PPBAdvance device."""
        data = await self._request(
            "/Driver/PPBAdvance/Dew/Auto/Aggressiveness",
            {"DriverUniqueKey": unique_key},
        )
        return self._extract_message(data)

    async def get_ppba_power_variable(self, unique_key: str) -> dict:
        """Return the variable power port state for a PPBAdvance device."""
        data = await self._request(
            "/Driver/PPBAdvance/Power/Variable", {"DriverUniqueKey": unique_key}
        )
        return self._extract_message(data)
