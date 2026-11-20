"""Read Google Classroom from Home Assistant."""

import voluptuous as vol

from homeassistant.const import Platform
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_entry_oauth2_flow, config_validation as cv
from homeassistant.helpers.service import (
    async_get_config_entry,
    async_register_admin_service,
)

from .const import DOMAIN
from .coordinator import ClassroomCoordinator

PLATFORMS = (Platform.CALENDAR, Platform.TODO)


async def async_setup(hass, config):
    """Register the actions once."""

    async def get_classes(call):
        """Return the cached class sections with their freshness."""
        entry = async_get_config_entry(hass, DOMAIN, call.data.get("config_entry_id"))
        coordinator = entry.runtime_data
        courses = coordinator.data
        if course_id := call.data.get("course_id"):
            courses = [course for course in courses if course["id"] == course_id]
            if not courses:
                raise ServiceValidationError("Class not found for this account")
        return {
            "last_synced": coordinator.last_update_success_time.isoformat(),
            "stale": not coordinator.last_update_success,
            "classes": courses,
        }

    async_register_admin_service(
        hass,
        DOMAIN,
        "get_classes",
        get_classes,
        schema=vol.Schema(
            {vol.Optional("config_entry_id"): cv.string, vol.Optional("course_id"): cv.string}
        ),
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_setup_entry(hass, entry):
    """Start polling after validating the first snapshot."""
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )
    oauth = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    coordinator = ClassroomCoordinator(hass, entry, oauth)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    # The action also needs polling when both optional entities are disabled.
    entry.async_on_unload(coordinator.async_add_listener(lambda: None))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Unload the entities and stop polling."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
