"""Share real login fixtures between authentication regression tests."""

import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken


class SessionTestCase(APITestCase):
    """Prepare a real account, login session and its signed cookie values."""

    def setUp(self):
        """Create one isolated account and log in through the public API."""
        self.password = secrets.token_urlsafe(24)
        self.user = get_user_model().objects.create_user(
            username='session_student', password=self.password,
        )
        self.credentials = {
            'username': self.user.username, 'password': self.password,
        }
        response = self.client.post(reverse('login'), self.credentials)
        self.access = response.cookies['access_token'].value
        self.refresh = response.cookies['refresh_token'].value

    def set_cookies(self, access=None, refresh=None):
        """Replace the cookie jar so each request uses exactly its fixtures."""
        self.client.cookies.clear()
        if access is not None:
            self.client.cookies['access_token'] = access
        if refresh is not None:
            self.client.cookies['refresh_token'] = refresh

    def expired_token(self, raw_token, token_class=AccessToken):
        """Sign an already expired copy of an otherwise valid test token."""
        token = token_class(raw_token)
        token.set_exp(lifetime=timedelta(seconds=-1))
        return str(token)

    def assert_unauthorized(self, response):
        """Check status, challenge and absence of newly issued cookies."""
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response['WWW-Authenticate'].startswith('Bearer'))
        self.assertFalse(response.cookies)

    def post_refresh(self):
        """Call refresh with the current cookie jar and an empty body."""
        return self.client.post(reverse('token-refresh'))

    def post_logout(self):
        """Call logout with the current cookie jar and an empty body."""
        return self.client.post(reverse('logout'))
