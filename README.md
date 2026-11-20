# Google Classroom for Home Assistant

A read-only integration for a student account. It syncs active classes on setup and every **4 hours** by default. Change **Refresh interval in hours** in the integration's options. For a manual refresh, run `homeassistant.update_entity` against the homework to-do list or deadline calendar.

## Install the integration

Copy the repository's `custom_components/google_classroom` directory into your Home Assistant configuration directory. The resulting path should be `/config/custom_components/google_classroom/manifest.json`. Restart Home Assistant before adding the integration.

## Set up Google Cloud

### 1. Choose which Google account does what

The **project owner** creates the app in Google Cloud. The **student account** signs in during Home Assistant setup and supplies the Classroom data. Before starting, sign in to [Google Classroom](https://classroom.google.com/) with the student account and confirm it shows the classes you want.

| Your situation | Google Auth Platform audience |
| --- | --- |
| A parent creates the Cloud project and a different Google account will sign in, or you are connecting multiple students | Start with **External** and **Testing**. Add each student's exact Google account as a test user. |
| One account will both create the Cloud project and sign in to Classroom, and that account can create projects | Use Google's **Personal mode** onboarding. Only the account that created the app can authorize it. Personal mode avoids the seven-day expiry for Testing tokens. |
| The school owns the project and its administrator is setting it up for accounts in the school's organization | The administrator can choose **Internal** if supported by the organization. |

A parent's guardian invitation allows access to summaries or eligible previews. For this integration, authorize with the account enrolled in the class. A school-managed account may need the administrator to configure the OAuth app even when the student is listed as a test user. [Google Auth Platform audiences](https://support.google.com/cloud/answer/15549945) · [Guardian access](https://support.google.com/edu/classroom/answer/6388136)

### 2. Create the project and enable the Classroom API

For **External** or **Internal** setup:

1. Open [Google Cloud Console](https://console.cloud.google.com/) as the project owner.
2. Open the project selector at the top and choose **New Project**. Use a name such as `Home Assistant Classroom`, choose the location if prompted, and select **Create**.
3. Select your new project in the project picker. Keep that project selected for all subsequent Google steps.
4. Open the [Google Classroom API page](https://console.cloud.google.com/apis/library/classroom.googleapis.com) and select **Enable**. If the page already shows **Manage**, the API is enabled for the selected project.

For **Personal mode**, begin at the [Personal mode setup page](https://console.cloud.google.com/auth/overview/personal) while signed in as the same account that will connect to Classroom. Create or select a Personal mode project. The wizard also creates your OAuth client. Use the application type and redirect URI in step 4, save the ID and secret, and enable the Classroom API in that project. Add the six scopes from step 3 under **Data Access** if the project offers scope configuration. Personal mode has no **Test users** step. [Google's Personal mode instructions](https://support.google.com/cloud/answer/15544987#quick-setup-for-personal-use)

### 3. Configure the Google consent screen

1. Open [Google Auth Platform → Branding](https://console.cloud.google.com/auth/branding). Select **Get started** if this is a new project.
2. Set **App name** to `Home Assistant Classroom`, select an account you control for **User support email**, and choose the audience from step 1. Enter an email for Google's project notices. Review the policy and finish creating the app.
3. If using **External / Testing**, open [Audience](https://console.cloud.google.com/auth/audience). Under **Test users**, select **Add users**, enter the student account that will sign in through Home Assistant, and save.
4. Open [Data Access](https://console.cloud.google.com/auth/scopes). Select **Add or remove scopes**, add the following six scopes, and save. Search for them in the picker or paste the full URLs into the manual entry box if offered. [Google's consent screen setup](https://developers.google.com/workspace/guides/configure-oauth-consent) · [Classroom scope reference](https://developers.google.com/workspace/classroom/guides/auth)

| Full scope | What the integration uses it for |
| --- | --- |
| `https://www.googleapis.com/auth/classroom.courses.readonly` | List active classes |
| `https://www.googleapis.com/auth/classroom.coursework.me.readonly` | Read assignments and the student's own submission states |
| `https://www.googleapis.com/auth/classroom.announcements.readonly` | Read published announcements |
| `https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly` | Read published materials |
| `https://www.googleapis.com/auth/classroom.topics.readonly` | Read topic names |
| `https://www.googleapis.com/auth/classroom.rosters.readonly` | Identify the signed-in account and read teacher and student names visible to it |

**Testing is for the first connection.** With these scopes, a Testing authorization and its refresh token expire after seven days. After confirming the connection works, review **Audience → Publish app** for a lasting External setup and sign in again. Google documents a limited-audience verification exception. An unverified app warning or school approval requirement can still apply. [Publishing status and token expiry](https://support.google.com/cloud/answer/15549945) · [Verification exceptions](https://support.google.com/cloud/answer/13464323)

### 4. Create an OAuth client

1. Open [Google Auth Platform → Clients](https://console.cloud.google.com/auth/clients) and select **Create client**.
2. Set **Application type** to **Web application** and name it `Home Assistant Classroom`.
3. In **Authorized redirect URIs**, select **Add URI**. For a standard Home Assistant installation with **My Home Assistant** enabled, enter this exact value with no trailing slash.

   ```text
   https://my.home-assistant.io/redirect/oauth
   ```

   Leave **Authorized JavaScript origins** empty. For an instance with **My Home Assistant** disabled, Home Assistant uses the URL you opened its UI at, followed by `/auth/external/callback`. Use the exact URI from the sign-in request and a URL permitted by Google's web client rules. [Home Assistant OAuth redirect behavior](https://github.com/home-assistant/core/blob/2026.11.2/homeassistant/helpers/config_entry_oauth2_flow.py#L94-L106) · [Google redirect URI rules](https://developers.google.com/identity/protocols/oauth2/web-server#uri-validation)

4. Select **Create**. Copy the **Client ID** and **Client secret** while the dialog is open, or download the JSON and keep it somewhere private. The ID usually ends in `.apps.googleusercontent.com`. The secret goes into Home Assistant's Application Credentials. Keep it out of GitHub and messages.

### 5. Link the student account in Home Assistant

1. Go to **Settings → Devices & services → Add integration**, then choose **Google Classroom**.
2. When Home Assistant asks for Application Credentials, enter a display name such as `Google Classroom`, the **Client ID**, and the **Client secret** from step 4. You can also enter them in **Settings → Devices & services → ⋮ → Application credentials**. [Home Assistant Application Credentials](https://www.home-assistant.io/integrations/application_credentials/)
3. In Google's sign-in window, choose the **student account**. If your browser selects a parent or personal account automatically, use **Use another account**. Review the requested read-only Classroom access and grant the permissions you want to use. The integration needs course and roster access to complete setup.
4. If **Link account to Home Assistant?** appears, confirm it shows your instance and select **Link Account**.
5. Back in Home Assistant, open **Developer tools → Actions**, run **Google Classroom: Get classes**, and check that the response lists a class you recognize. Open that class in Classroom and compare a known assignment. If the roster section is unavailable, check `unavailable_sections` in the response.

### Troubleshoot Google sign-in

| What you see | What to check |
| --- | --- |
| `redirect_uri_mismatch` | Open the **specific OAuth client** under **Clients**. Confirm the exact callback, including HTTPS, path, and trailing slash, is under **Authorized redirect URIs**. |
| Google says only approved testers can access the app | Under **Audience → Test users**, verify the exact student email. Then check which account was selected in Google's sign-in window. |
| `client_user_mismatch` or `org_internal` | A Personal app requires its creator's account. An Internal app requires an account inside the owning organization. Check the project audience against the account you selected. |
| `admin_policy_enforced`, a school-managed **Access blocked** screen, or Classroom access denied with the API enabled | Ask the school administrator to review third-party access for the **OAuth Client ID** and the six scopes above, and confirm that **Classroom API** access is enabled for the student's organizational unit. Share the Client ID and error text with the administrator. Keep the secret private. [School third-party app access](https://support.google.com/edu/classroom/answer/15163043) · [Classroom data access setting](https://support.google.com/edu/classroom/answer/6250906) |
| Home Assistant asks you to sign in again after about a week | Check whether the project is still **External / Testing**. Testing tokens expire after seven days. |
| Setup succeeds but the class list is empty | Open Classroom in the same browser account and confirm you can see an active class in which that account is enrolled as a student. |

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
