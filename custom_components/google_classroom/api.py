"""Read Google Classroom without downloading grades or student work."""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

API_URL = "https://classroom.googleapis.com/v1"
Request = Callable[[str, dict[str, str]], Awaitable[dict[str, Any]]]
QUOTA_REASONS = {
    "rateLimitExceeded",
    "userRateLimitExceeded",
    "quotaExceeded",
    "dailyLimitExceeded",
    "RESOURCE_EXHAUSTED",
}

# Keep the response models small, especially for rosters and submissions.
CLASS_SECTIONS = {
    "announcements": (
        "announcements",
        "announcements",
        "id,text,alternateLink,creationTime,updateTime",
    ),
    "coursework": (
        "courseWork",
        "courseWork",
        "id,title,description,alternateLink,topicId,workType,dueDate,dueTime",
    ),
    "materials": (
        "courseWorkMaterials",
        "courseWorkMaterial",
        "id,title,description,alternateLink,topicId",
    ),
    "topics": ("topics", "topic", "topicId,name"),
    "teachers": ("teachers", "teachers", "profile(name(fullName))"),
    "students": ("students", "students", "profile(name(fullName))"),
    "submissions": (
        "courseWork/-/studentSubmissions",
        "studentSubmissions",
        "courseWorkId,state",
    ),
}


class ClassroomError(Exception):
    """An error returned by Google Classroom."""

    def __init__(self, status: int, reason: str = "") -> None:
        """Store a sanitized error."""
        super().__init__(f"Classroom returned HTTP {status}")
        self.status = status
        self.reason = reason


class ClassroomClient:
    """Read a snapshot for a student account."""

    def __init__(self, request: Request) -> None:
        """Use the caller's authenticated transport."""
        self.request = request

    async def list_items(
        self,
        path: str,
        key: str,
        fields: str,
        **params: str,
    ) -> list[dict[str, Any]]:
        """Read all pages, including after an empty page."""
        items = []
        params["fields"] = f"nextPageToken,{key}({fields})"
        while True:
            page = await self.request(path, params)
            items.extend(page.get(key, []))
            if not (token := page.get("nextPageToken")):
                return items
            params["pageToken"] = token

    async def fetch_courses(self) -> list[dict[str, Any]]:
        """Read each visible section of the student's active courses."""
        courses = await self.list_items(
            "courses",
            "courses",
            "id,name,section,alternateLink",
            studentId="me",
            courseStates="ACTIVE",
        )
        for course in courses:
            await self._fetch_sections(course)
        return courses

    async def _fetch_sections(self, course: dict[str, Any]) -> None:
        """Represent permissions explicitly and leave transient errors to retry."""
        base = f"courses/{quote(course['id'], safe='')}"
        unavailable = {}
        for section, (path, key, fields) in CLASS_SECTIONS.items():
            params = {"userId": "me"} if section == "submissions" else {}
            try:
                course[section] = await self.list_items(
                    f"{base}/{path}", key, fields, **params
                )
            except ClassroomError as err:
                if err.status == 403 and err.reason not in QUOTA_REASONS:
                    unavailable[section] = "permission_denied"
                elif err.status == 404:
                    unavailable[section] = "not_found"
                else:
                    raise
        for role in ("teachers", "students"):
            if role in course:
                course[role] = [
                    member["profile"]["name"]["fullName"]
                    for member in course[role]
                    if member.get("profile", {}).get("name", {}).get("fullName")
                ]
        submissions = {
            item["courseWorkId"]: item.get("state")
            for item in course.pop("submissions", [])
        }
        for work in course.get("coursework", []):
            work["submissionState"] = submissions.get(work["id"])
            due = due_datetime(work)
            work["due"] = due.isoformat() if due else None
        course["unavailable_sections"] = unavailable


def due_datetime(work: dict[str, Any]) -> datetime | None:
    """Combine Google's UTC deadline date and time."""
    if not (day := work.get("dueDate")):
        return None
    clock = work.get("dueTime", {"hours": 23, "minutes": 59})
    return datetime(
        day["year"],
        day["month"],
        day["day"],
        clock.get("hours", 0),
        clock.get("minutes", 0),
        clock.get("seconds", 0),
        clock.get("nanos", 0) // 1000,
        tzinfo=UTC,
    )
