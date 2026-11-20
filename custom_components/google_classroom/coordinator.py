"""Shared per-account Classroom refresh."""

from datetime import timedelta
import logging

from aiohttp import ClientError, ClientTimeout

from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    OAuth2TokenRequestError,
    OAuth2TokenRequestReauthError,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator,
    UpdateFailed,
)

from .api import API_URL, ClassroomClient, ClassroomError
from .const import CONF_REFRESH_HOURS, DEFAULT_REFRESH_HOURS, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_get_json(session, token, path, params):
    """Make a Classroom API request and omit API error bodies from logging."""
    async with session.get(
        f"{API_URL}/{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=ClientTimeout(total=20),
    ) as response:
        if response.status >= 400:
            reason = ""
            if response.status == 403 and response.content_type == "application/json":
                error = (await response.json()).get("error", {})
                reason = error.get("status", "")
                if reason != "RESOURCE_EXHAUSTED" and (reasons := error.get("errors")):
                    reason = reasons[0].get("reason", "")
            raise ClassroomError(response.status, reason)
        return await response.json()


class ClassroomCoordinator(TimestampDataUpdateCoordinator):
    """Update the whole account once per polling interval."""

    def __init__(self, hass, entry, oauth):
        """Create the shared client."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                hours=entry.options.get(CONF_REFRESH_HOURS, DEFAULT_REFRESH_HOURS)
            ),
        )
        self.oauth = oauth
        self.session = async_get_clientsession(hass)
        self.client = ClassroomClient(self._request)

    async def _request(self, path, params):
        """Read a page with the current token."""
        return await async_get_json(
            self.session, self.oauth.token["access_token"], path, params
        )

    async def _async_update_data(self):
        """Refresh the token and return a complete account snapshot."""
        try:
            await self.oauth.async_ensure_token_valid()
            courses = await self.client.fetch_courses()
        except ClassroomError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed("Google rejected the Classroom token") from err
            raise UpdateFailed(str(err)) from err
        except OAuth2TokenRequestReauthError as err:
            raise ConfigEntryAuthFailed("Google Classroom needs reauthentication") from err
        except (ClientError, OAuth2TokenRequestError, TimeoutError) as err:
            raise UpdateFailed("Could not reach Google Classroom") from err
        return courses
