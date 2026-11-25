"""Check registration responses, validation and password storage."""

import secrets

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class RegistrationTests(APITestCase):
    """Exercise public registration without authentication shortcuts."""

    def setUp(self):
        """Prepare a valid account request with a temporary password."""
        self.url = reverse('register')
        self.password = secrets.token_urlsafe(24)
        self.data = {
            'username': 'quiz_student', 'email': 'student@example.com',
            'password': self.password, 'confirmed_password': self.password,
        }

    def test_registration_creates_user_with_hashed_password(self):
        """Return only the success message and store a password hash."""
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data, {'detail': 'User created successfully!'},
        )
        user = get_user_model().objects.get(username=self.data['username'])
        self.assertEqual(user.email, self.data['email'])
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password, self.password)
        self.assertFalse(response.cookies)

    def test_required_fields_reject_missing_blank_and_null(self):
        """Reject incomplete requests without creating any accounts."""
        for field in self.data:
            for value in ('missing', '', None):
                with self.subTest(field=field, value=value):
                    data = {key: item for key, item in self.data.items()
                            if key != field}
                    if value != 'missing':
                        data[field] = value
                    response = self.client.post(self.url, data, format='json')
                    self.assertEqual(response.status_code, 400)
                    self.assertIn(field, response.data)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_duplicate_username_is_rejected(self):
        """Keep the original account when its username is reused."""
        self.client.post(self.url, self.data, format='json')
        data = {**self.data, 'email': 'another@example.com'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_duplicate_email_is_case_insensitive(self):
        """Reject an existing email even if its letter case changes."""
        self.client.post(self.url, self.data, format='json')
        data = {
            **self.data, 'username': 'another', 'email': 'STUDENT@example.com',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_invalid_email_and_username_are_rejected(self):
        """Reject malformed identifiers without persisting a user."""
        for field, value in [('email', 'invalid'), ('username', 'bad name!')]:
            with self.subTest(field=field):
                response = self.client.post(
                    self.url, {**self.data, field: value}, format='json',
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_password_mismatch_is_rejected(self):
        """Require an exact match for the confirmation field."""
        data = {**self.data, 'confirmed_password': self.password + 'x'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirmed_password', response.data)
        self.assertFalse(get_user_model().objects.exists())

    def test_password_whitespace_is_preserved(self):
        """Hash the supplied password without silently trimming spaces."""
        password = f' {self.password} '
        data = {
            **self.data, 'password': password, 'confirmed_password': password,
        }
        self.client.post(self.url, data, format='json')
        user = get_user_model().objects.get(username=self.data['username'])
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.check_password(self.password))

    def test_account_privileges_cannot_be_supplied(self):
        """Ignore client attempts to make the registered user privileged."""
        data = {**self.data, 'is_staff': True, 'is_superuser': True}
        self.client.post(self.url, data, format='json')
        user = get_user_model().objects.get(username=self.data['username'])
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_bad_json_is_rejected(self):
        """Return a controlled error for a malformed JSON request."""
        response = self.client.post(
            self.url, '{', content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(get_user_model().objects.exists())

    def test_other_methods_are_not_allowed(self):
        """Keep registration limited to POST and preflight OPTIONS."""
        for method in ('get', 'put', 'patch', 'delete'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, 405)
