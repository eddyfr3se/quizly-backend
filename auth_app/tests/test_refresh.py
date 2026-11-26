"""Check cookie refresh without relying on a valid access token."""

from django.test import override_settings
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from auth_app.models import AuthSession
from .session_helpers import SessionTestCase


@override_settings(ROOT_URLCONF='auth_app.tests.urls')
class RefreshTests(SessionTestCase):
    """Verify refresh success, failure cases and cookie-only behavior."""

    def test_refresh_issues_only_a_new_access_cookie(self):
        """Replace access without extending the refresh lifetime."""
        response = self.post_refresh()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'detail': 'Token refreshed'})
        self.assertEqual(set(response.cookies), {'access_token'})
        self.assertEqual(response['Cache-Control'], 'no-store')
        token = AccessToken(response.cookies['access_token'].value)
        self.assertEqual(
            token['session_id'], RefreshToken(self.refresh)['jti'],
        )
        self.assertNotEqual(token['jti'], AccessToken(self.access)['jti'])
        cookie = self.client.cookies['refresh_token']
        self.assertEqual(cookie.value, self.refresh)

    def test_refresh_works_with_missing_expired_or_invalid_access(self):
        """Only the refresh cookie determines whether refresh is allowed."""
        for access in (None, 'invalid', self.expired_token(self.access)):
            with self.subTest(access_present=access is not None):
                self.set_cookies(access=access, refresh=self.refresh)
                response = self.post_refresh()
                self.assertEqual(response.status_code, 200)
                probe = self.client.get(reverse('session-probe'))
                self.assertEqual(probe.status_code, 200)

    def test_refresh_does_not_accept_body_or_access_as_credentials(self):
        """Require refresh cookies rather than body or access credentials."""
        self.set_cookies(access=self.access)
        self.assert_unauthorized(self.post_refresh())
        self.set_cookies()
        response = self.client.post(
            reverse('token-refresh'), {'refresh': self.refresh}, format='json',
        )
        self.assert_unauthorized(response)

    def test_bad_expired_wrong_type_and_blacklisted_refresh(self):
        """Reject each invalid refresh form with HTTP 401 and no new cookie."""
        tokens = (
            'invalid', self.refresh[:-8] + 'tampered', self.access,
            self.expired_token(self.refresh, RefreshToken),
        )
        for token in tokens:
            self.set_cookies(refresh=token)
            self.assert_unauthorized(self.post_refresh())
        RefreshToken(self.refresh).blacklist()
        self.set_cookies(refresh=self.refresh)
        self.assert_unauthorized(self.post_refresh())

    def test_inactive_account_cannot_refresh(self):
        """Do not issue new access tokens to a deactivated account."""
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.assert_unauthorized(self.post_refresh())

    def test_missing_or_mismatched_session_is_rejected(self):
        """Require the original refresh identifier and a live session row."""
        token = RefreshToken(self.refresh)
        token['session_id'] = 'different-session'
        self.set_cookies(refresh=str(token))
        self.assert_unauthorized(self.post_refresh())
        AuthSession.objects.all().delete()
        self.set_cookies(refresh=self.refresh)
        self.assert_unauthorized(self.post_refresh())

    def test_untrusted_origins_cannot_refresh(self):
        """Reject browser origins without replacing either token."""
        for origin in ('https://example.org', 'null'):
            response = self.client.post(
                reverse('token-refresh'), HTTP_ORIGIN=origin,
            )
            self.assertEqual(response.status_code, 403)
            self.assertFalse(response.cookies)
        self.assertEqual(AuthSession.objects.count(), 1)

    def test_refresh_cookie_policy(self):
        """Preserve HttpOnly, path, SameSite and lifetime on renewal."""
        with override_settings(JWT_COOKIE_SECURE=True):
            cookie = self.post_refresh().cookies['access_token']
        self.assertTrue(cookie['httponly'])
        self.assertTrue(cookie['secure'])
        self.assertEqual(cookie['path'], '/')
        self.assertEqual(cookie['samesite'], 'Lax')
        self.assertEqual(cookie['max-age'], 300)

    def test_other_methods_are_rejected(self):
        """Expose only the documented POST operation and preflight."""
        for method in ('get', 'put', 'patch', 'delete'):
            response = getattr(self.client, method)(reverse('token-refresh'))
            self.assertEqual(response.status_code, 405)
