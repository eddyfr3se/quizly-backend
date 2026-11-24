# Quizly Backend

Django REST backend for the Quizly frontend of the Developer Akademie.
It turns a YouTube URL into a quiz with ten questions: the audio track is
downloaded, transcribed locally and sent to Gemini Flash to build the quiz.

Status: project setup. API endpoints are added step by step.

## Requirements

- Python 3.12 (Whisper does not support newer versions reliably)
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

Start it with Live Server on http://127.0.0.1:5500 and open it through
`127.0.0.1`, not `localhost`, so the authentication cookies are sent.
