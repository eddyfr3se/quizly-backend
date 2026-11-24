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
