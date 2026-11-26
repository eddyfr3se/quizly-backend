"""Expose a protected probe only when tests select this URL configuration."""

from django.urls import path
from rest_framework.response import Response
from rest_framework.views import APIView

from core.urls import urlpatterns as application_urls


class SessionProbeView(APIView):
    """Exercise global authentication and permissions without quiz models."""

    def get(self, request):
        """Return the authenticated account identifier."""
        return Response({'user_id': request.user.pk})

    def post(self, request):
        """Exercise the origin policy for an authenticated write request."""
        return Response({'user_id': request.user.pk})


urlpatterns = application_urls + [
    path(
        'api/test-session/', SessionProbeView.as_view(), name='session-probe',
    ),
]
