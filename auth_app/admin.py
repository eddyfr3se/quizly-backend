"""Inspect active authentication sessions."""

from django.contrib import admin

from .models import AuthSession


@admin.register(AuthSession)
class AuthSessionAdmin(admin.ModelAdmin):
    """Display active logins without allowing token identifiers to change."""

    list_display = ('user', 'expires_at')
    search_fields = ('user__username',)
    readonly_fields = ('refresh_jti', 'user', 'expires_at')
    list_select_related = ('user',)

    def has_add_permission(self, request):
        """Only the login endpoint may create authentication sessions."""
        return False
