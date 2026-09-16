"""Module containing core app's custom permission classes."""

import logging

from django.conf import settings
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class CanAccessApiPermission(BasePermission):
    """Allow API access only to the tiers that pay for it.

    **Switched on in two steps, because the first one is unmeasurable from
    here.** The check was written when the API shipped and then left returning
    `True`, so every caller has had access for as long as the endpoint has
    existed. Turning it on is not a configuration change to them - it is the day
    their integration stops working, and the access logs cannot say which tier
    any of them holds.

    So `API_TIER_ENFORCED` starts false. The tier is evaluated on every request
    exactly as it will be when enforced, and a caller who would be refused is
    *logged and let through*. That turns "who breaks?" from a guess into a
    query against a log, answered by the same code that will later do the
    refusing - rather than by a second implementation that could disagree with
    it.

    Measured before this was written: 2,068,287 public API requests over five
    weeks of access logs, of which 1,011,635 were already 401 and 983,244 were
    redirects. **Only 70,969 succeeded** - about 2,000 a day. The population
    that enforcement can break is that one, not the two million, and shadow mode
    is how we learn its shape before taking anything away.

    **A missing profile is refused, not waved through.** `JWTAuthentication`
    resolves a real user, but a user without a profile row is a broken account
    rather than a free one, and a permission check that fails open is not a
    permission check.
    """

    def has_permission(self, request, view):
        """Return whether this request's tier may use the API.

        :param request: DRF request object
        :type request: :class:`rest_framework.request.Request`
        :param view: the view being dispatched
        :type view: :class:`rest_framework.views.APIView`
        :return: bool
        """
        # **Exempt before anything else, including the tier read.** These are
        # credentials that cannot be reissued on our schedule - the mobile app
        # ships its token inside a released binary - so they must not depend on
        # an account's tier staying where it is.
        if getattr(request.user, "pk", None) in getattr(
            settings, "API_TIER_EXEMPT_USER_IDS", frozenset()
        ):
            return True

        profile = getattr(request.user, "profile", None)
        allowed = bool(profile and profile.can_access_api())
        if allowed:
            return True

        if not getattr(settings, "API_TIER_ENFORCED", False):
            # Logged at warning so it survives a production log level that hides
            # info, and carries what a decision needs: who, what tier, and what
            # they were reaching for.
            logger.warning(
                "api tier shadow: would refuse user=%s permission=%s path=%s",
                getattr(request.user, "pk", None),
                getattr(profile, "permission", None),
                request.path,
            )
            return True

        return False
