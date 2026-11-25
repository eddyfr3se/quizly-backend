"""Validate registration and login data."""

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate account details and hash the new user's password."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirmed_password = serializers.CharField(
        write_only=True, trim_whitespace=False,
    )

    class Meta:
        """Declare the registration fields explicitly."""

        model = get_user_model()
        fields = ('username', 'email', 'password', 'confirmed_password')

    def validate_email(self, value):
        """Reject an email address already used by another account."""
        if get_user_model().objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email already exists.')
        return value

    def validate(self, attrs):
        """Require the password confirmation to match exactly."""
        if attrs['password'] != attrs['confirmed_password']:
            raise serializers.ValidationError(
                {'confirmed_password': 'Passwords do not match.'},
            )
        return attrs

    def create(self, validated_data):
        """Create the account using Django's password hashing."""
        validated_data.pop('confirmed_password')
        return get_user_model().objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Authenticate an active account without exposing why login failed."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        """Attach the authenticated user or return a generic error."""
        user = authenticate(
            request=self.context.get('request'),
            username=attrs['username'], password=attrs['password'],
        )
        if user is None:
            raise AuthenticationFailed('Invalid username or password.')
        attrs['user'] = user
        return attrs
