# Google Classroom for Home Assistant

A read-only integration for a student account. It syncs active classes on setup and every **4 hours** by default. Change **Refresh interval in hours** in the integration's options. For a manual refresh, run `homeassistant.update_entity` against the homework to-do list or deadline calendar.

## Install and connect

1. Copy the `google_classroom` directory to `custom_components/` in your Home Assistant configuration directory. Restart Home Assistant.
2. Enable the [Google Classroom API](https://console.cloud.google.com/apis/library/classroom.googleapis.com) in a Google Cloud project. Create a **Web application** OAuth client with `https://my.home-assistant.io/redirect/oauth` as an authorized redirect URI if you use My Home Assistant. Follow the [Google Calendar OAuth setup](https://www.home-assistant.io/integrations/google/) for the Home Assistant redirect and Application Credentials screens. Use the Classroom API and scopes listed below.
3. In **Settings → Devices & services → Add integration**, choose **Google Classroom**, enter the OAuth client credentials, and sign in with the student account. The school may need to allow the client and Classroom scopes. External projects in Testing mode issue refresh tokens that expire in seven days. [Google's app audience settings](https://support.google.com/cloud/answer/15549945) explain the available modes.

The component requests these read-only Classroom scopes, each prefixed with `https://www.googleapis.com/auth/`.

| Scope | Use |
| --- | --- |
| `classroom.courses.readonly` | List active classes |
| `classroom.coursework.me.readonly` | Read assignments and the student's own submission states |
| `classroom.announcements.readonly` | Read published announcements |
| `classroom.courseworkmaterials.readonly` | Read published materials |
| `classroom.topics.readonly` | Read topic names |
| `classroom.rosters.readonly` | Identify the signed-in account and read visible teacher and student names |

## Use class data

The integration creates a homework to-do list and a deadline calendar for each connected account. The calendar includes dated assignments regardless of submission state. The to-do list shows work with unknown submission state separately from open and completed work. A Classroom return is treated as completed for the to-do list. Use Classroom to confirm whether a returned assignment needs revision.

Try **Google Classroom: Get classes** in **Developer tools → Actions**. The action returns the cached data for all active classes or for a single class ID. Select the account when there are multiple entries. It returns class announcements, assignments and questions, published materials, topics, and the names Google makes visible in each roster. The action includes `last_synced`, `stale`, and each class's `unavailable_sections`.

In an automation or script, store the action response in a variable.

```yaml
- action: google_classroom.get_classes
  response_variable: classroom
```

For homework reminders, check `classroom.stale` and the relevant class's `unavailable_sections` before using submission data. At the default interval, a new announcement or submission may take up to four hours to appear. Classroom does not expose excused, missing, and teacher-marked-complete states as distinct API statuses.

Teacher and classmate names are available through the administrator-only class action. The component requests names without roster emails or photos. Classwork titles and links are visible through the standard Home Assistant entities to users who can read them. Classroom links open in Google and require the viewer's own access.
