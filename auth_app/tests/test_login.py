"""Check login credentials, response fields and JWT cookie policies."""

import secrets

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class LoginTests(APITestCase):
    """Exercise login with real password checks and JWT signatures."""

    def setUp(self):
        """Create an active test account with a temporary password."""
        self.url = reverse('login')
        self.password = secrets.token_urlsafe(24)
        self.user = get_user_model().objects.create_user(
            username='quiz_student', email='student@example.com',
            password=self.password,
        )
        self.data = {'username': self.user.username, 'password': self.password}

    def test_success_returns_exact_account_response(self):
        """Keep password hashes and token values out of the JSON body."""
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'detail': 'Login successfully!',
            'user': {
                'id': self.user.pk, 'username': self.user.username,
                'email': self.user.email,
            },
        })
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_cookies_contain_valid_tokens_for_the_same_user(self):
        """Verify signatures, token types and the account identifier."""
        response = self.client.post(self.url, self.data, format='json')
        access = AccessToken(response.cookies['access_token'].value)
        refresh = RefreshToken(response.cookies['refresh_token'].value)
        self.assertEqual(str(access['user_id']), str(self.user.pk))
        self.assertEqual(access['user_id'], refresh['user_id'])
        self.assertNotEqual(access['jti'], refresh['jti'])
        self.assertEqual(access['exp'] - access['iat'], 300)
        self.assertEqual(refresh['exp'] - refresh['iat'], 86400)

    @override_settings(JWT_COOKIE_SECURE=False)
    def test_local_cookie_attributes(self):
        """Allow local HTTP with HttpOnly cookies scoped to this host."""
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(
            set(response.cookies), {'access_token', 'refresh_token'},
        )
        for cookie in response.cookies.values():
            self.assertTrue(cookie['httponly'])
            self.assertFalse(cookie['secure'])
            self.assertEqual(cookie['samesite'], 'Lax')
            self.assertEqual(cookie['path'], '/')
            self.assertEqual(cookie['domain'], '')
        self.assertEqual(response.cookies['access_token']['max-age'], 300)
        self.assertEqual(response.cookies['refresh_token']['max-age'], 86400)

    @override_settings(JWT_COOKIE_SECURE=True)
    def test_secure_cookie_setting_is_respected(self):
        """Mark both authentication cookies Secure when configured."""
        response = self.client.post(self.url, self.data, format='json')
        for cookie in response.cookies.values():
            self.assertTrue(cookie['secure'])

    def test_invalid_credentials_use_the_same_generic_error(self):
        """Reject wrong passwords, unknown usernames and inactive accounts."""
        cases = [
            {**self.data, 'password': secrets.token_urlsafe(24)},
            {**self.data, 'username': 'unknown'},
        ]
        for data in cases:
            with self.subTest(username=data['username']):
                self.assert_invalid_login(data)
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.assert_invalid_login(self.data)

    def assert_invalid_login(self, data):
        """Check the documented credential failure without issuing cookies."""
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {
            'detail': 'Invalid username or password.',
        })
        self.assertEqual(response['WWW-Authenticate'], 'Bearer')
        self.assertFalse(response.cookies)

    def test_missing_blank_and_null_fields_are_bad_requests(self):
        """Reject structurally incomplete login requests without tokens."""
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
                    self.assertFalse(response.cookies)

    def test_repeated_login_issues_new_tokens(self):
        """Do not reuse token identifiers between successful logins."""
        first = self.client.post(self.url, self.data, format='json')
        second = self.client.post(self.url, self.data, format='json')
        for name in ('access_token', 'refresh_token'):
            self.assertNotEqual(
                first.cookies[name].value, second.cookies[name].value,
            )

    def test_stale_credentials_do_not_block_public_login(self):
        """Allow credentials to replace an invalid cookie or header."""
        self.client.cookies['access_token'] = 'invalid'
        response = self.client.post(
            self.url, self.data, format='json',
            HTTP_AUTHORIZATION='Bearer invalid',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_whitespace_is_not_trimmed(self):
        """Require the actual stored password including surrounding spaces."""
        password = f' {self.password} '
        self.user.set_password(password)
        self.user.save(update_fields=['password'])
        response = self.client.post(
            self.url, {**self.data, 'password': password}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_invalid_login(self.data)

    def test_other_methods_are_not_allowed(self):
        """Keep login limited to POST and preflight OPTIONS."""
        for method in ('get', 'put', 'patch', 'delete'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, 405)
