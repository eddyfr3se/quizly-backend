"""Check immediate logout revocation and cookie removal."""

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from auth_app.models import AuthSession
from .session_helpers import SessionTestCase


@override_settings(ROOT_URLCONF='auth_app.tests.urls')
class LogoutTests(SessionTestCase):
    """Verify logout revokes this login without invalidating other logins."""

    def test_logout_response_and_cookie_removal(self):
        """Return the exact documented message and expire both cookies."""
        response = self.post_logout()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'detail': 'Log-Out successfully! All Tokens will be deleted. '
                      'Refresh token is now invalid.',
        })
        self.assertEqual(
            set(response.cookies), {'access_token', 'refresh_token'},
        )
        self.assert_cookies_cleared(response)

    def assert_cookies_cleared(self, response):
        """Check the values and scope of both expired cookies."""
        for cookie in response.cookies.values():
            self.assertEqual(cookie.value, '')
            self.assertEqual(cookie['max-age'], 0)
            self.assertEqual(cookie['path'], '/')
            self.assertEqual(cookie['samesite'], 'Lax')

    def test_refresh_is_blacklisted_and_session_removed(self):
        """Persist the refresh blacklist and delete the active login row."""
        jti = RefreshToken(self.refresh)['jti']
        self.post_logout()
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=jti).exists(),
        )
        self.assertFalse(AuthSession.objects.exists())

    def test_original_and_renewed_access_are_immediately_rejected(self):
        """Reject every access token from this login after logout."""
        renewed = self.post_refresh().cookies['access_token'].value
        self.assertGreater(
            AccessToken(self.access)['exp'], int(timezone.now().timestamp()),
        )
        self.post_logout()
        for token in (self.access, renewed):
            self.set_cookies(access=token)
            response = self.client.get(reverse('session-probe'))
            self.assert_unauthorized(response)
        self.set_cookies(refresh=self.refresh)
        self.assert_unauthorized(self.post_refresh())

    def test_logout_without_refresh_still_revokes_it(self):
        """Blacklist refresh using access when the refresh cookie is absent."""
        self.set_cookies(access=self.access)
        self.assertEqual(self.post_logout().status_code, 200)
        self.set_cookies(refresh=self.refresh)
        self.assert_unauthorized(self.post_refresh())

    def test_logout_with_missing_expired_or_invalid_access(self):
        """Let a valid refresh cookie finish logout after access expiry."""
        for access in (None, 'invalid', self.expired_token(self.access)):
            with self.subTest(access_present=access is not None):
                response = self.client.post(reverse('login'), self.credentials)
                refresh = response.cookies['refresh_token'].value
                self.set_cookies(access=access, refresh=refresh)
                self.assertEqual(self.post_logout().status_code, 200)
                self.set_cookies(refresh=refresh)
                self.assert_unauthorized(self.post_refresh())

    def test_other_login_of_the_same_user_remains_valid(self):
        """Revoke one browser session while preserving a second login."""
        response = self.client.post(reverse('login'), self.credentials)
        other_access = response.cookies['access_token'].value
        other_refresh = response.cookies['refresh_token'].value
        self.set_cookies(access=self.access, refresh=self.refresh)
        self.post_logout()
        self.set_cookies(access=other_access, refresh=other_refresh)
        response = self.client.get(reverse('session-probe'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post_refresh().status_code, 200)
        self.assertEqual(AuthSession.objects.count(), 1)

    def test_no_valid_credential_and_repeated_logout_are_unauthorized(self):
        """Require a valid cookie credential for successful logout."""
        self.set_cookies()
        self.assert_unauthorized(self.post_logout())
        self.set_cookies(access='invalid', refresh='invalid')
        self.assert_unauthorized(self.post_logout())
        self.set_cookies(access=self.access, refresh=self.refresh)
        self.assertEqual(self.post_logout().status_code, 200)
        self.assert_unauthorized(self.post_logout())

    def test_untrusted_origin_does_not_revoke_the_session(self):
        """Reject foreign logout without revoking the legitimate login."""
        response = self.client.post(
            reverse('logout'), HTTP_ORIGIN='https://example.org',
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(AuthSession.objects.count(), 1)
        response = self.client.get(reverse('session-probe'))
        self.assertEqual(response.status_code, 200)

    def test_other_methods_are_rejected(self):
        """Keep logout a POST operation without GET side effects."""
        for method in ('get', 'put', 'patch', 'delete'):
            response = getattr(self.client, method)(reverse('logout'))
            self.assertEqual(response.status_code, 405)
        self.assertEqual(AuthSession.objects.count(), 1)
