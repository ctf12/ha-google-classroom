"""Constants for Google Classroom."""

DOMAIN = "google_classroom"
CONF_REFRESH_HOURS = "refresh_hours"
DEFAULT_REFRESH_HOURS = 4
SCOPES = tuple(
    f"https://www.googleapis.com/auth/classroom.{scope}.readonly"
    for scope in (
        "courses",
        "coursework.me",
        "announcements",
        "courseworkmaterials",
        "topics",
        "rosters",
    )
)
