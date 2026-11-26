# Quizly Backend

Django REST backend for the Quizly frontend of the Developer Akademie.
It turns a YouTube URL into a quiz with ten questions: the audio track is
downloaded, transcribed locally and sent to Gemini Flash to build the quiz.

Status: registration, cookie authentication, refresh and logout are implemented
and tested. Quiz endpoints are planned for the following stages.

See [Installation](#installation) to get started and the
[development diary](DEVELOPMENT_DIARY.md) for verified progress and open work.

## Requirements

- Python 3.12 (the version used for local setup and Whisper practice)
- FFmpeg installed globally (required by yt-dlp and Whisper)
- deno (JavaScript runtime used by yt-dlp)
- A Gemini API key from https://ai.google.dev/

macOS with Homebrew:

```bash
brew install ffmpeg python@3.12 deno
```

## Installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Generate a Django secret key and put it into `.env` in double quotes:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Add your Gemini API key to `.env` as well. Django loads `.env`
automatically; keep this file private.

Create the database tables:

```bash
python manage.py migrate
```

## Start the backend

```bash
python manage.py runserver
```

The API runs at http://127.0.0.1:8000/api/.

## Frontend

The frontend is provided separately by the Developer Akademie:
https://github.com/Developer-Akademie-Backendkurs/project.Quizly

Reviewed frontend revision: `ae8e8637e39d328e3b8a55670db77f121deffb49`.
Keep its checkout in a separate directory, such as `../Quizly_Frontend`.
Frontend files are not included in this backend repository.

Start it with Live Server on http://127.0.0.1:5500 and open it through
`127.0.0.1`, not `localhost`, so the authentication cookies are sent.

## API reference

The [official endpoint documentation](https://cdn.developerakademie.com/courses/Backend/EndpointDoku/index.html?name=quizly)
defines the requests, responses and permissions used for acceptance checks.

## Authentication

- `POST /api/register/`: send `username`, `email`, `password` and
  `confirmed_password`. Success returns HTTP 201; invalid fields return 400.
- `POST /api/login/`: send `username` and `password`. Success returns HTTP 200
  with account data. Invalid credentials return a generic HTTP 401 response;
  missing or invalid request fields return 400.
- Login sets `access_token` (5 minutes) and `refresh_token` (1 day) as
  HttpOnly, SameSite=Lax cookies with path `/`. Tokens are not in the JSON body.
- Cookies use Secure when `DJANGO_DEBUG=False`. Local HTTP development uses
  `DJANGO_DEBUG=True`. Browser clients must send `credentials: "include"`.
- Authentication requests with an Origin header must come from the backend
  or a configured frontend origin. Other origins return HTTP 403.
- Protected API views authenticate through the `access_token` cookie.
  Missing, invalid, expired or revoked credentials return HTTP 401.
- `POST /api/token/refresh/`: an empty request with the `refresh_token` cookie
  sets a new access cookie and returns `{"detail": "Token refreshed"}`.
  It works even when the access cookie is absent or expired.
- `POST /api/logout/`: revokes the current login, blacklists its refresh token
  and deletes both cookies. A valid refresh cookie can complete logout when
  access has expired. Other logins remain valid.

Each login has a small server-side session record. Its identifier is included
in both signed tokens. Logout removes this record, so all access tokens from
that login are rejected immediately, including tokens issued by refresh.
After upgrading from the initial cookie-login implementation, run migrations
and log in again; older tokens have no session record.

## Tests

Run the Django tests in the activated backend environment:

```bash
python manage.py test
```

For repeatable Postman checks, start the disposable test backend in a separate
terminal with the backend environment activated:

```bash
python -m auth_app.tests.server
```

It uses a temporary database on port 8001. Stop it with Ctrl+C after testing.
Run the collections in order with the Postman CLI, or import them into Postman:

```bash
postman collection run postman/quizly-auth.postman_collection.json --env-var base_url=http://127.0.0.1:8001/api/ --no-report-events
postman collection run postman/quizly-sessions.postman_collection.json --no-report-events
```

Each collection creates a randomly named account. Passwords and tokens exist
only as runtime variables. The session collection uses a protected test probe
that is available only on the disposable test server, not in the normal API.
See [test results](postman/TEST_RESULTS.md) for the verified scope and counts.
