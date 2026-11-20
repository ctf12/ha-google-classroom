"""Read-only calendar of Classroom deadlines."""

from datetime import timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api import due_datetime


async def async_setup_entry(hass, entry, async_add_entities):
    """Add one deadline calendar per student account."""
    async_add_entities([HomeworkCalendar(entry)])


class HomeworkCalendar(CoordinatorEntity, CalendarEntity):
    """Publish timed calendar events for Classroom deadlines."""

    def __init__(self, entry):
        """Identify the deadline calendar."""
        super().__init__(entry.runtime_data)
        self._attr_name = f"{entry.title} Classroom deadlines"
        self._attr_unique_id = f"{entry.unique_id}_classroom_deadlines"

    def _events(self):
        """Build sorted events from due dates in the current snapshot."""
        events = []
        for course in self.coordinator.data:
            for work in course.get("coursework", []):
                if due := due_datetime(work):
                    start = dt_util.as_local(due)
                    events.append(
                        CalendarEvent(
                            uid=f"{course['id']}:{work['id']}",
                            start=start,
                            end=dt_util.as_local(due + timedelta(minutes=1)),
                            summary=work["title"],
                            description=work.get("alternateLink"),
                            location=course["name"],
                        )
                    )
        return sorted(events, key=lambda event: event.start.timestamp())

    @property
    def event(self):
        """Return the current or next deadline."""
        now = dt_util.utcnow().timestamp()
        return next((event for event in self._events() if event.end.timestamp() > now), None)

    async def async_get_events(self, hass, start_date, end_date):
        """Return deadlines that overlap the requested interval."""
        return [
            event
            for event in self._events()
            if event.end.timestamp() > start_date.timestamp()
            and event.start.timestamp() < end_date.timestamp()
        ]
