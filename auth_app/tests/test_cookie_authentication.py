"""Check signature validation and server-side session enforcement."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from auth_app.models import AuthSession
from .session_helpers import SessionTestCase


@override_settings(ROOT_URLCONF='auth_app.tests.urls')
class CookieAuthenticationTests(SessionTestCase):
    """Exercise the global authentication for protected endpoints."""

    def probe(self, **headers):
        """Send a request through a view using the global API defaults."""
        return self.client.get(reverse('session-probe'), **headers)

    def test_probe_is_absent_from_application_urls(self):
        """Do not expose test-only endpoints through the normal API."""
        with override_settings(ROOT_URLCONF='core.urls'):
            response = self.client.get('/api/test-session/')
        self.assertEqual(response.status_code, 404)

    def test_access_cookie_authenticates(self):
        """Accept a signed access cookie belonging to an active session."""
        self.set_cookies(access=self.access)
        response = self.probe()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'user_id': self.user.pk})

    def test_missing_cookie_and_header_only_are_unauthorized(self):
        """Do not accept header credentials in place of the required cookie."""
        self.set_cookies()
        self.assert_unauthorized(self.probe())
        self.assert_unauthorized(
            self.probe(HTTP_AUTHORIZATION=f'Bearer {self.access}'),
        )

    def test_invalid_expired_and_wrong_type_cookies(self):
        """Reject bad signatures, malformed, expired and wrong-type tokens."""
        tokens = (
            'invalid', self.access[:-8] + 'tampered', self.refresh,
            self.expired_token(self.access),
        )
        for token in tokens:
            with self.subTest(token_type=token[:6]):
                self.set_cookies(access=token)
                self.assert_unauthorized(self.probe())

    def test_missing_session_claim_is_rejected(self):
        """Require a login identifier as well as a valid signature."""
        token = AccessToken(self.access)
        del token['session_id']
        self.set_cookies(access=str(token))
        self.assert_unauthorized(self.probe())

    def test_deleted_or_expired_session_is_rejected(self):
        """Reject a session after revocation or after its refresh lifetime."""
        self.set_cookies(access=self.access)
        expired = timezone.now() - timedelta(days=1)
        AuthSession.objects.update(expires_at=expired)
        self.assert_unauthorized(self.probe())
        AuthSession.objects.all().delete()
        self.assert_unauthorized(self.probe())

    def test_token_cannot_use_another_users_session(self):
        """Bind sessions to their owners as well as their identifiers."""
        other = get_user_model().objects.create_user(username='other_student')
        token = AccessToken(self.access)
        token['user_id'] = other.pk
        self.set_cookies(access=str(token))
        self.assert_unauthorized(self.probe())

    def test_inactive_and_deleted_accounts_are_rejected(self):
        """Reject accounts that are no longer active or no longer exist."""
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.assert_unauthorized(self.probe())
        self.user.delete()
        self.assert_unauthorized(self.probe())

    def test_write_origin_policy_applies_to_protected_views(self):
        """Restrict browser writes to the configured frontend."""
        url = reverse('session-probe')
        for origin, code in [('https://example.org', 403),
                             ('http://127.0.0.1:5500', 200)]:
            with self.subTest(origin=origin):
                response = self.client.post(url, HTTP_ORIGIN=origin)
                self.assertEqual(response.status_code, code)
        response = self.client.post(url, HTTP_SEC_FETCH_SITE='cross-site')
        self.assertEqual(response.status_code, 403)
