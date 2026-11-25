# Quizly Backend

Django REST backend for the Quizly frontend of the Developer Akademie.
It turns a YouTube URL into a quiz with ten questions: the audio track is
downloaded, transcribed locally and sent to Gemini Flash to build the quiz.

Status: registration and cookie login are implemented and tested.
Refresh, logout and quiz endpoints are planned for the following stages.

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
- Cookie authentication for protected endpoints, refresh and logout are
  not implemented yet.

## Tests

Run the Django tests in the activated backend environment:

```bash
python manage.py test
```

Import [the auth collection](postman/quizly-auth.postman_collection.json) into
Postman or run it with the Postman CLI:

```bash
postman collection run postman/quizly-auth.postman_collection.json --no-report-events
```

Run the collection against a disposable local database: each run creates a
randomly named account. Credentials are generated at runtime. The collection's
`base_url` defaults to `http://127.0.0.1:8000/api/` and can be overridden.
See [test results](postman/TEST_RESULTS.md) for the verified scope and counts.
