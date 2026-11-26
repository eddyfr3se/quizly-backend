"""Run a disposable local backend for the saved Postman collections."""

import os
import tempfile
from pathlib import Path

import django
from django.conf import settings
from django.core.management import call_command


def main():
    """Keep test accounts and the session probe out of the regular backend."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    with tempfile.TemporaryDirectory(prefix='quizly-auth-tests-') as directory:
        database = Path(directory) / 'db.sqlite3'
        settings.DATABASES['default']['NAME'] = str(database)
        settings.ROOT_URLCONF = 'auth_app.tests.urls'
        django.setup()
        call_command('migrate', verbosity=0)
        call_command('runserver', '127.0.0.1:8001', use_reloader=False)


if __name__ == '__main__':
    main()
