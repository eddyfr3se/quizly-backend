"""Reject browser authentication requests from untrusted origins."""

from django.conf import settings
from rest_framework.permissions import BasePermission


class HasTrustedOrigin(BasePermission):
    """Allow configured frontend origins and requests without an Origin."""

    message = 'Untrusted request origin.'

    def has_permission(self, request, view):
        """Check the browser Origin before changing authentication state."""
        origin = request.headers.get('Origin')
        fetch_site = request.headers.get('Sec-Fetch-Site')
        if origin is None and fetch_site == 'cross-site':
            return False
        own_origin = f'{request.scheme}://{request.get_host()}'
        return origin is None or origin in (
            own_origin, *settings.CORS_ALLOWED_ORIGINS,
        )
