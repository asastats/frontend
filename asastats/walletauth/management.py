"""Account address-management operations (set-primary, remove, login toggle).

Pure service functions over the :class:`LinkedAddress` registry, kept free of
HTTP concerns so they are exhaustively unit-testable. The views in
:mod:`walletauth.management_views` enforce authentication, step-up (a fresh
signature from the current primary for privilege/access-expanding operations)
and self-scoping before calling these.

Invariants preserved here:
- exactly one primary per account, always login-capable;
- permission/subscription/governance follow the primary, re-derived on change;
- the primary cannot be removed (a replacement must be promoted first).
"""

import logging

from walletauth.models import LinkedAddress

logger = logging.getLogger(__name__)


class CannotRemovePrimary(Exception):
    """Raised when removal targets the primary address."""


class CannotDisablePrimaryLogin(Exception):
    """Raised when login is disabled on the primary address."""


def set_primary(profile, target):
    """Promote ``target`` (an existing secondary) to primary; demote the old one.

    Mirrors the new primary onto ``Profile.address`` and re-derives permission
    from it. The previous primary stays linked as a (still login-capable)
    secondary. A no-op if ``target`` is already primary.

    :param profile: the owning profile
    :type profile: core.models.Profile
    :param target: the row to promote (must belong to ``profile``)
    :type target: walletauth.models.LinkedAddress
    :var refreshed: whether permission re-derived in-band
    :type refreshed: bool
    :return: whether the permission refresh succeeded (False ⇒ pending)
    :rtype: bool
    """
    if target.is_primary:
        return True

    # Demote first (zero primaries momentarily), then promote: never two at once.
    LinkedAddress.objects.filter(profile=profile, is_primary=True).update(
        is_primary=False
    )
    target.is_primary = True
    target.login_enabled = True
    target.save(update_fields=["is_primary", "login_enabled"])

    # Mirror onto Profile and re-derive permission. Persist the address before
    # update_authorized: Profile.save() clears authorized/permission on an
    # address change, so re-authorizing afterwards re-derives cleanly.
    profile.address = target.address
    profile.save()
    refreshed = profile.update_authorized(target.authorized, method=target.auth_method)
    logger.info(
        "walletauth: primary changed (permission_pending=%s)", not refreshed
    )
    return refreshed


def remove_address(profile, linked):
    """Remove a secondary address from ``profile``.

    :param profile: the owning profile (for symmetry/logging)
    :type profile: core.models.Profile
    :param linked: the row to remove
    :type linked: walletauth.models.LinkedAddress
    :raises CannotRemovePrimary: when ``linked`` is the primary
    """
    if linked.is_primary:
        raise CannotRemovePrimary("Set another address as primary before removing it")
    linked.delete()


def set_login_enabled(profile, linked, enabled):
    """Enable or disable sign-in for a linked address.

    :param profile: the owning profile (for symmetry/logging)
    :type profile: core.models.Profile
    :param linked: the row to update
    :type linked: walletauth.models.LinkedAddress
    :param enabled: desired ``login_enabled`` value
    :type enabled: bool
    :raises CannotDisablePrimaryLogin: when disabling login on the primary
    """
    if linked.is_primary and not enabled:
        raise CannotDisablePrimaryLogin("The primary address must remain login-capable")
    linked.login_enabled = enabled
    linked.save(update_fields=["login_enabled"])
