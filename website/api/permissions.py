"""Module containing core app's custom permission classes."""

import logging

from django.conf import settings
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class CanAccessApiPermission(BasePermission):
    """Allow API access only to the tiers that pay for it.

    **`API_TIER_ENFORCED` starts false and the refusal is a log line.** The tier
    is evaluated on every request exactly as it will be when enforced, and a
    caller who would be refused is logged and let through - so "who breaks?" is
    a query against a log rather than a guess, answered by the same code that
    will later do the refusing.

    A missing profile is refused rather than waved through: a user without a
    profile row is a broken account, not a free one.
    """

    def has_permission(self, request, view):
        """Return whether this request's tier may use the API.

        :param request: DRF request object
        :type request: :class:`rest_framework.request.Request`
        :param view: the view being dispatched
        :type view: :class:`rest_framework.views.APIView`
        :return: bool
        """
        # Exempt before the tier is even read. These credentials cannot be
        # reissued on our schedule - the mobile app ships its token inside a
        # released binary - so they must not depend on an account's tier.
        if getattr(request.user, "pk", None) in getattr(
            settings, "API_TIER_EXEMPT_USER_IDS", frozenset()
        ):
            return True

        profile = getattr(request.user, "profile", None)
        allowed = bool(profile and profile.can_access_api())
        if allowed:
            return True

        if not getattr(settings, "API_TIER_ENFORCED", False):
            # Warning rather than info, so it survives the production log level,
            # and it carries what a decision needs: who, what tier, what for.
            logger.warning(
                "api tier shadow: would refuse user=%s permission=%s path=%s",
                getattr(request.user, "pk", None),
                getattr(profile, "permission", None),
                request.path,
            )
            return True

        return False
