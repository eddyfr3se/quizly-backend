"""Restrict quiz details and changes to their owner."""

from rest_framework.permissions import BasePermission


class IsQuizOwner(BasePermission):
    """Allow an authenticated user to access only their own quiz."""

    def has_object_permission(self, request, view, obj):
        """Check ownership after resolving the requested quiz."""
        return obj.owner_id == request.user.pk
