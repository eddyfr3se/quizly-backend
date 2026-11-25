"""Expose public registration and cookie login endpoints."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import HasTrustedOrigin
from .serializers import LoginSerializer, RegistrationSerializer
from .utils import create_login_response


class RegistrationView(APIView):
    """Create an account without requiring an existing login."""

    authentication_classes = []
    permission_classes = [HasTrustedOrigin]
    http_method_names = ['post', 'options']

    def post(self, request):
        """Validate registration data and return the documented response."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'User created successfully!'},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate credentials and issue HttpOnly JWT cookies."""

    authentication_classes = []
    permission_classes = [HasTrustedOrigin]
    http_method_names = ['post', 'options']

    def get_authenticate_header(self, request):
        """Keep invalid credentials as HTTP 401 instead of DRF's HTTP 403."""
        return 'Bearer'

    def post(self, request):
        """Validate credentials and return account data with auth cookies."""
        serializer = LoginSerializer(
            data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        return create_login_response(serializer.validated_data['user'])
