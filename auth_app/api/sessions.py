"""Issue, validate and revoke login sessions."""

from datetime import datetime, timezone as datetime_timezone

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken, OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.models import AuthSession


@transaction.atomic
def issue_refresh_token(user):
    """Create an active session and attach its identifier to both tokens."""
    refresh = RefreshToken.for_user(user)
    refresh['session_id'] = refresh['jti']
    AuthSession.objects.create(
        refresh_jti=refresh['jti'], user=user,
        expires_at=datetime.fromtimestamp(
            refresh['exp'], datetime_timezone.utc,
        ),
    )
    return refresh


def get_auth_session(token, user):
    """Require an unexpired server-side session owned by this token's user."""
    try:
        return AuthSession.objects.get(
            refresh_jti=token.get('session_id'), user=user,
            expires_at__gt=timezone.now(),
        )
    except AuthSession.DoesNotExist as error:
        raise AuthenticationFailed('Invalid or expired session.') from error


def read_refresh_token(raw_token):
    """Reject malformed, expired or blacklisted refresh cookies as HTTP 401."""
    try:
        token = RefreshToken(raw_token)
    except TokenError as error:
        raise InvalidToken('Invalid refresh token.') from error
    if token.get('session_id') != token['jti']:
        raise InvalidToken('Invalid refresh session.')
    return token


@transaction.atomic
def revoke_session(session):
    """Blacklist the refresh token and invalidate all access tokens at once."""
    for token in OutstandingToken.objects.filter(jti=session.refresh_jti):
        BlacklistedToken.objects.get_or_create(token=token)
    session.delete()
