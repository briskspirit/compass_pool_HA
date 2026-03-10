"""API client for Compass WiFi pool heater cloud service."""

import logging

import aiohttp

from .const import API_URL

_LOGGER = logging.getLogger(__name__)


class CompassApiError(Exception):
    """General API error."""


class CompassAuthError(CompassApiError):
    """Authentication error."""


class CompassApi:
    """Client for the Compass WiFi / ICM Controls cloud API."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._username = username
        self._password = password
        self._session = session
        self._token: str | None = None
        self._owns_session = session is None

    async def _ensure_session(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True

    async def _request(self, payload: dict) -> dict:
        await self._ensure_session()
        try:
            async with self._session.post(
                API_URL,
                json=payload,
                headers={"Content-Type": "application/json;charset=utf-8"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    raise CompassApiError(f"HTTP {resp.status}")
                return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise CompassApiError(f"Connection error: {err}") from err

    async def login(self) -> str:
        """Authenticate and obtain a session token."""
        data = await self._request(
            {
                "action": "login",
                "username": self._username,
                "password": self._password,
            }
        )
        if data.get("result") != "success":
            raise CompassAuthError(
                f"Login failed: {data.get('result', 'unknown error')}"
            )
        self._token = data["token"]
        _LOGGER.debug("Login successful, token obtained")
        return self._token

    async def _authenticated_request(self, payload: dict) -> dict:
        """Make an authenticated API request, refreshing token if needed."""
        if not self._token:
            await self.login()

        payload["token"] = self._token
        data = await self._request(payload)

        # Handle token expiry by re-authenticating once
        if data.get("result") in ("token_expired", "invalid_token", "error"):
            _LOGGER.debug("Token expired or invalid, re-authenticating")
            await self.login()
            payload["token"] = self._token
            data = await self._request(payload)

        if data.get("result") != "success":
            raise CompassApiError(f"API error: {data.get('result', 'unknown')}")

        return data

    async def get_devices(self) -> list[dict]:
        """Get list of devices associated with the account."""
        data = await self._authenticated_request(
            {
                "action": "getPasDevices",
                "additionalFields": "special parameter holder",
            }
        )
        return data.get("devices", [])

    async def get_device_detail(self, thermostat_key: str) -> dict:
        """Get full device status including all register fields."""
        data = await self._authenticated_request(
            {
                "action": "thermostatGetDetail",
                "thermostatKey": thermostat_key,
            }
        )
        return data.get("detail", {})

    async def set_fields(self, thermostat_key: str, fields: dict) -> dict:
        """Set one or more device register fields.

        All field values are sent as strings per the API protocol.
        """
        str_fields = {k: str(v) for k, v in fields.items()}
        _LOGGER.debug("Setting fields on %s: %s", thermostat_key, str_fields)
        return await self._authenticated_request(
            {
                "action": "thermostatSetFields",
                "thermostatKey": thermostat_key,
                "fields": str_fields,
            }
        )

    async def close(self) -> None:
        """Close the HTTP session if we own it."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()
            self._session = None
