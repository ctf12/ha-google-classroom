"""Read-only homework list."""

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api import due_datetime

STATUS = {
    "NEW": TodoItemStatus.NEEDS_ACTION,
    "CREATED": TodoItemStatus.NEEDS_ACTION,
    "RECLAIMED_BY_STUDENT": TodoItemStatus.NEEDS_ACTION,
    "TURNED_IN": TodoItemStatus.COMPLETED,
    "RETURNED": TodoItemStatus.COMPLETED,
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Add one homework list per student account."""
    async_add_entities([HomeworkList(entry)])


class HomeworkList(CoordinatorEntity, TodoListEntity):
    """Show Classroom assignments and their last known submission states."""

    def __init__(self, entry):
        """Identify the homework list."""
        super().__init__(entry.runtime_data)
        self._attr_name = f"{entry.title} homework"
        self._attr_unique_id = f"{entry.unique_id}_homework"

    @property
    def todo_items(self):
        """Build the list from the current snapshot."""
        return [
            TodoItem(
                uid=f"{course['id']}:{work['id']}",
                summary=work["title"],
                status=STATUS.get(work["submissionState"]),
                due=dt_util.as_local(due) if (due := due_datetime(work)) else None,
                description="\n".join(
                    text for text in (course["name"], work.get("alternateLink")) if text
                ),
            )
            for course in self.coordinator.data
            for work in course.get("coursework", [])
        ]
