# Development diary

## Day 1 – Tools and local practice

- Installed Python 3.12, FFmpeg and deno. A separate local practice
  environment contains yt-dlp, Whisper and the Gemini client.
- Earlier practice produced a downloaded audio file and a transcript.
  A successful Gemini quiz generation was reported during that session;
  it was not repeated in the checks below.
- A handwritten example response is available for offline development.
  It is a fixture, not output from a verified live generation request.
- Still open: confirm the Module 11 videos and notes on cookie login,
  authentication and refresh behavior.

## Day 2 – Backend setup

- Created the Django project with `core`, `auth_app` and `quiz_app`,
  including separate API URL modules.
- Configured automatic environment loading, SQLite, REST framework and
  credentialed CORS for the frontend on port 5500.
- Added the installation guide, dependency versions and configuration example.
- Applied the standard Django migrations and committed the setup as
  `dd66a8d` (`Set up Quizly Django backend`).
- Published the existing setup commit to the public backend repository:
  <https://github.com/eddyfr3se/quizly-backend>.
- Cloned the supplied frontend into the separate sibling directory
  `Quizly_Frontend`, retaining its Academy remote. Reviewed source revision:
  `ae8e8637e39d328e3b8a55670db77f121deffb49`.
- Confirmed the frontend API address is `http://127.0.0.1:8000/api/`.
  Frontend files remain outside the backend repository and its uploads.
- Use the official endpoint documentation as the acceptance checklist.
  No endpoint is marked complete until its responses and permissions pass
  the relevant checks. All nine operations are currently pending.

### Verification on 24 November 2026

- Django's system check passed; all existing standard migrations are applied.
- Dependency checks passed for the backend and local practice environments.
- The Django test client received HTTP 200 from the admin login page.
  `/admin/` redirected to login. No admin account exists yet.
- CORS preflights returned the expected origin and credentials headers for
  the two configured local origins. An unrelated origin received no CORS
  permission headers.
- API paths returned HTTP 404, as expected for empty API URL modules.
  Registration, login, token refresh, logout and quiz operations are pending.
- The Django test command discovered zero tests. No application test suite
  has passed at this stage.
- The offline example contained ten questions with four distinct options
  each and answers present among the options. Full validation is still pending.
- Reviewed the tracked setup files and Git exclusions before publication.
  Environment files, databases and local practice materials were excluded.

### Remaining work and next step

- Start the separate frontend on port 5500 for the authentication browser checks.
- Confirm the remaining learning notes before implementing authentication.
- Replace the backend Gemini configuration placeholder before pipeline testing.
- Create a local admin account before testing quiz and question management.
- Implement registration and cookie login in Day 3, followed by refresh,
  logout, token revocation and authentication tests in Day 4.
- Continue updating this diary after every daily stage with completed changes,
  actual checks and results, remaining work and the next step.

### Day 2 closeout – 24 November 2026

- The technical setup stage is complete: the backend is published, the
  supplied frontend is checked out separately, and its revision is recorded.
- The installation guide, daily progress record and endpoint acceptance
  reference are in place. Application endpoints remain unimplemented.
- The working tree was clean before this closeout entry, and the Git
  whitespace check passed. No application tests were rerun for this
  documentation-only update.
- Next session: confirm the outstanding learning notes, then begin Day 3
  with registration and login using HttpOnly JWT cookies.

## Day 3 – Registration and cookie login – 25 November 2026

- Implemented public registration with explicit serializer fields, duplicate
  username/email checks and exact password confirmation. Django hashes passwords.
- Implemented username/password login with the documented account response.
  Wrong credentials and inactive accounts receive the same HTTP 401 message.
- Added HttpOnly access/refresh cookies with lifetimes of 5 minutes and 1 day,
  SameSite=Lax, host-only scope and Secure outside local debug mode.
- Kept token values out of JSON responses and disabled login-response caching.
- Restricted browser authentication requests to trusted origins. Kept helpers
  outside views and added short English class and method docstrings.
- Added 23 Django tests and a reusable Postman collection containing 33 requests.
  The Postman run passed all 99 assertions using a disposable database on port
  8001; the existing development database on port 8000 was not changed.
- Checked migration consistency, PEP 8 for new API/tests, function lengths
  and Git whitespace. Detailed scope is in `postman/TEST_RESULTS.md`.
- Checked off registration and login in the official endpoint documentation
  in Safari. The remaining seven operations are still open.
- Checked frontend registration and login in a separate test browser using a
  temporary frontend copy pointing to the disposable backend. Both redirects
  worked. Browser storage contained both HttpOnly cookies, and JavaScript
  could not read them. The quiz-list request still returned the expected 404.
- Protected cookie authentication, refresh, logout and immediate token
  revocation are next on Day 4. The complete quiz workflow remains pending.
- Closed the test browser and stopped both temporary servers after the checks;
  their disposable database and frontend copy were removed automatically.

## Day 4 – Cookie authentication, refresh and logout – 26 November 2026

- Added access-cookie authentication with signature, expiry, account status
  and server-side session checks. Protected requests without valid cookies
  return HTTP 401; header-only credentials do not replace the cookie.
- Added an active session record per login and enabled the refresh blacklist.
  Logout removes the session and blacklists refresh, immediately invalidating
  original and renewed access tokens. Other logins remain valid.
- Implemented cookie refresh independently of access expiry. Logout can use
  a valid refresh cookie if access is missing or expired. Browser writes from
  untrusted origins are rejected before any token or session changes.
- Applied the session and blacklist migrations to the development database.
  Existing accounts were preserved. Earlier login cookies require a new login.
- Ran checks in sequence: Django tests, the existing Postman regression,
  the new session collection, then the browser workflow. Final results:
  50 Django tests and 65 Postman requests with 158 assertions passed.
- Verified automatic frontend refresh without a login redirect, logout back
  to login, cookie deletion and HTTP 401 after logout. Used only disposable
  test data and a temporary frontend copy; the supplied checkout is unchanged.
- Added a reusable disposable test server. Its protected probe exists only
  in the test URL configuration and is absent from the normal application API.
- Checked off refresh and logout in the official endpoint documentation:
  four of nine operations complete. Details are in `postman/TEST_RESULTS.md`.
- Stopped the test browser and temporary servers. Next: Day 5, quiz/question
  models, admin and owner-restricted list/detail/update/delete endpoints.
