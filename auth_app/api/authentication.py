"""Read JWT cookies and require a live login session."""

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from .sessions import get_auth_session, read_refresh_token


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate protected requests using only the access cookie."""

    def authenticate(self, request):
        """Check the signature, expiry, active account and login session."""
        raw_token = request.COOKIES.get('access_token')
        if not raw_token:
            return None
        token = self.get_validated_token(raw_token)
        user = self.get_user(token)
        get_auth_session(token, user)
        return user, token


class CookieRefreshAuthentication(JWTAuthentication):
    """Validate refresh cookies independently of an expired access cookie."""

    def authenticate(self, request):
        """Require a valid refresh token and the matching active session."""
        raw_token = request.COOKIES.get('refresh_token')
        if not raw_token:
            return None
        token = read_refresh_token(raw_token)
        user = self.get_user(token)
        get_auth_session(token, user)
        return user, token


class LogoutCookieAuthentication(CookieJWTAuthentication):
    """Allow logout with a valid access cookie or a valid refresh cookie."""

    def authenticate(self, request):
        """Fall back to refresh authentication when access has expired."""
        try:
            result = super().authenticate(request)
        except AuthenticationFailed:
            result = None
        return result or CookieRefreshAuthentication().authenticate(request)
