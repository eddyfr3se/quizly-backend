"""Build authentication responses and their HttpOnly cookies."""

from django.conf import settings
from rest_framework.response import Response
from rest_framework_simplejwt.settings import api_settings

from .sessions import issue_refresh_token


def set_token_cookie(response, name, token, lifetime):
    """Store a token for its lifetime using the configured cookie policy."""
    response.set_cookie(
        name, str(token), max_age=int(lifetime.total_seconds()),
        httponly=True, secure=settings.JWT_COOKIE_SECURE,
        samesite='Lax', path='/',
    )


def get_login_data(user):
    """Return the documented account fields without token values."""
    return {
        'detail': 'Login successfully!',
        'user': {
            'id': user.pk, 'username': user.username, 'email': user.email,
        },
    }


def create_login_response(user):
    """Issue an access and refresh token as HttpOnly cookies."""
    refresh = issue_refresh_token(user)
    response = Response(get_login_data(user))
    set_token_cookie(
        response, 'access_token', refresh.access_token,
        api_settings.ACCESS_TOKEN_LIFETIME,
    )
    set_token_cookie(
        response, 'refresh_token', refresh,
        api_settings.REFRESH_TOKEN_LIFETIME,
    )
    response['Cache-Control'] = 'no-store'
    return response


def create_refresh_response(token):
    """Replace only the access cookie without exposing the JWT in JSON."""
    response = Response({'detail': 'Token refreshed'})
    set_token_cookie(
        response, 'access_token', token.access_token,
        api_settings.ACCESS_TOKEN_LIFETIME,
    )
    response['Cache-Control'] = 'no-store'
    return response


def create_logout_response():
    """Expire both cookies with the same path and SameSite policy."""
    response = Response({
        'detail': 'Log-Out successfully! All Tokens will be deleted. '
                  'Refresh token is now invalid.',
    })
    for name in ('access_token', 'refresh_token'):
        response.delete_cookie(name, path='/', samesite='Lax')
    response['Cache-Control'] = 'no-store'
    return response
