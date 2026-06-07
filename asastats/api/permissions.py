"""Module containing core app's custom permission classes."""

import logging

from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class CanAccessApiPermission(BasePermission):
    """Permission check if user has acceess to API."""

    def has_permission(self, request, view):
        """FIXME: implement commented out routine after a month passes in production.

        Also change from JWTStatelessUserAuthentication to JWTAuthentication afterwards.
        """
        # return request.user.profile.can_access_api()
        return True
