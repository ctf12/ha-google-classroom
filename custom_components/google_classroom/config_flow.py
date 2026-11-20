"""Configure OAuth and the per-account polling interval."""

import logging

from aiohttp import ClientError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ClassroomError
from .const import CONF_REFRESH_HOURS, DEFAULT_REFRESH_HOURS, DOMAIN, SCOPES
from .coordinator import async_get_json

_LOGGER = logging.getLogger(__name__)


class ClassroomConfigFlow(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Link the student's Google account."""

    DOMAIN = DOMAIN

    @property
    def logger(self):
        """Return the config-flow logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self):
        """Ask Google for an offline read-only grant."""
        return {
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_oauth_create_entry(self, data):
        """Validate the account and use its stable Classroom profile ID."""
        token = data["token"]
        if not token.get("refresh_token"):
            return self.async_abort(reason="missing_refresh_token")
        try:
            profile = await async_get_json(
                async_get_clientsession(self.hass),
                token["access_token"],
                "userProfiles/me",
                {"fields": "id,name(fullName)"},
            )
            await async_get_json(
                async_get_clientsession(self.hass),
                token["access_token"],
                "courses",
                {"studentId": "me", "courseStates": "ACTIVE", "pageSize": "1"},
            )
        except ClassroomError as err:
            return self.async_abort(
                reason="classroom_access_denied" if err.status == 403 else "cannot_connect"
            )
        except (ClientError, TimeoutError):
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(profile["id"])
        if self.source == config_entries.SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch(reason="wrong_account")
            return self.async_update_reload_and_abort(self._get_reauth_entry(), data=data)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=profile.get("name", {}).get("fullName") or "Google Classroom",
            data=data,
        )

    async def async_step_reauth(self, entry_data):
        """Start a new grant for the existing entry."""
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Set up polling preferences."""
        return ClassroomOptionsFlow()


class ClassroomOptionsFlow(config_entries.OptionsFlowWithReload):
    """Set the refresh interval in hours."""

    async def async_step_init(self, user_input=None):
        """Save the interval and reload the integration."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_REFRESH_HOURS,
                        default=self.config_entry.options.get(
                            CONF_REFRESH_HOURS, DEFAULT_REFRESH_HOURS
                        ),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.25, max=168))
                }
            ),
        )
