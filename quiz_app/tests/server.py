"""Run a disposable backend with quiz fixtures for API and browser checks."""

import json
import os
import secrets
import tempfile
from pathlib import Path

import django
from django.conf import settings
from django.core.management import call_command


def create_account(username):
    """Create a fictional fixture account with a runtime-only password."""
    from django.contrib.auth import get_user_model
    password = secrets.token_urlsafe(24)
    user = get_user_model().objects.create_user(
        username=username, password=password, email=f'{username}@example.com',
    )
    return user, password


def create_quiz(owner, title):
    """Prepare ten questions without downloading or generating any content."""
    from quiz_app.models import Question, Quiz
    quiz = Quiz.objects.create(
        owner=owner, title=title, description='Local test quiz',
        video_url='https://www.youtube.com/watch?v=jNQXAC9IVRw',
    )
    for index in range(10):
        Question.objects.create(
            quiz=quiz, question_title=f'Practice question {index + 1}',
            question_options=['A', 'B', 'C', 'D'], answer='A',
        )
    return quiz


def write_environment(directory, values):
    """Keep fixture credentials in a temporary Postman environment file."""
    path = Path(directory) / 'environment.json'
    data = {'name': 'Quizly local fixtures', 'values': [
        {'key': key, 'value': str(value), 'enabled': True,
         'type': 'secret' if 'password' in key else 'default'}
        for key, value in values.items()
    ]}
    path.write_text(json.dumps(data))
    path.chmod(0o600)
    print(f'Postman environment: {path}', flush=True)


def create_fixtures(directory):
    """Create two users, owned/foreign quizzes and a deletion fixture."""
    owner, password = create_account('quiz_test_owner')
    other, other_password = create_account('quiz_test_other')
    quiz = create_quiz(owner, 'Learning quiz')
    foreign = create_quiz(other, 'Private quiz')
    disposable = create_quiz(owner, 'Delete fixture')
    write_environment(directory, {
        'base_url': 'http://127.0.0.1:8001/api/',
        'username': owner.username, 'password': password,
        'other_username': other.username, 'other_password': other_password,
        'quiz_id': quiz.pk, 'foreign_quiz_id': foreign.pk,
        'delete_quiz_id': disposable.pk,
    })


def main():
    """Run the normal API with seeded data in a temporary database."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    with tempfile.TemporaryDirectory(prefix='quizly-quiz-tests-') as directory:
        database = Path(directory) / 'db.sqlite3'
        settings.DATABASES['default']['NAME'] = str(database)
        django.setup()
        call_command('migrate', verbosity=0)
        create_fixtures(directory)
        call_command('runserver', '127.0.0.1:8001', use_reloader=False)


if __name__ == '__main__':
    main()
