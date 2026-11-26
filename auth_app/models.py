"""Track active logins so logout immediately revokes their access tokens."""

from django.conf import settings
from django.db import models


class AuthSession(models.Model):
    """Link one refresh token and its access tokens to an active login."""

    refresh_jti = models.CharField(max_length=255, primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='auth_sessions',
    )
    expires_at = models.DateTimeField()

    def __str__(self):
        """Identify the account and the expiry in the admin."""
        return f'{self.user_id}: {self.expires_at}'
