"""Check browser origin restrictions and CORS for authentication."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


class AuthenticationOriginTests(APITestCase):
    """Check origin guards on both public authentication endpoints."""

    def test_untrusted_and_null_origins_are_rejected(self):
        """Reject foreign origins before validating credentials."""
        for name in ('login', 'register'):
            for origin in ('https://example.org', 'null'):
                with self.subTest(name=name, origin=origin):
                    response = self.client.post(
                        reverse(name), {}, format='json', HTTP_ORIGIN=origin,
                    )
                    self.assertEqual(response.status_code, 403)
                    self.assertFalse(response.cookies)
        self.assertFalse(get_user_model().objects.exists())

    def test_trusted_and_same_origins_reach_validation(self):
        """Allow both configured frontends and same-origin requests."""
        origins = (
            'http://127.0.0.1:5500', 'http://localhost:5500',
            'http://testserver',
        )
        for name in ('login', 'register'):
            for origin in origins:
                with self.subTest(name=name, origin=origin):
                    response = self.client.post(
                        reverse(name), {}, format='json', HTTP_ORIGIN=origin,
                    )
                    self.assertEqual(response.status_code, 400)

    def test_frontend_preflight_allows_credentials(self):
        """Allow frontend JSON requests with cookies."""
        for name in ('login', 'register'):
            response = self.client.options(
                reverse(name), HTTP_ORIGIN='http://127.0.0.1:5500',
                HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
                HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type',
            )
            self.assert_preflight_allowed(response)

    def assert_preflight_allowed(self, response):
        """Check the response headers needed for credentialed requests."""
        self.assertEqual(response.status_code, 200)
        headers = response.headers
        self.assertEqual(headers['Access-Control-Allow-Credentials'], 'true')
        self.assertEqual(
            headers['Access-Control-Allow-Origin'], 'http://127.0.0.1:5500',
        )
