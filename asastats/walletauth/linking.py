"""Registry write operations for multi-address accounts.

Centralizes how a *verified* address becomes a :class:`LinkedAddress` row so the
authorize flow (:mod:`walletauth.views`) and the link flow
(:mod:`walletauth.link_views`) share one consistent, testable code path. Every
write deduplicates on the canonical form and refuses to let one on-chain account
belong to two profiles. Permission/subscription/governance still derive solely
from the primary (``Profile.address``); secondary rows confer nothing.
"""

import logging
from collections import namedtuple

from django.utils import timezone

from walletauth.addresses import canonical_for, max_secondary_addresses
from walletauth.models import LinkedAddress

logger = logging.getLogger(__name__)

#: Outcome of :func:`link_address`.
LinkResult = namedtuple(
    "LinkResult", ["linked_address", "is_primary", "permission_pending"]
)


class AddressAlreadyLinked(Exception):
    """Raised when an address is already linked to a *different* account."""


class SecondaryLimitReached(Exception):
    """Raised when an account already holds the maximum secondary addresses."""


def _chain_of(address):
    """Infer the chain of a stored address.

    :param address: a stored/display address
    :type address: str
    :return: ``"evm"`` for ``0x…`` addresses, otherwise ``"algorand"``
    :rtype: str
    """
    return "evm" if address.lower().startswith("0x") else "algorand"


def _auth_method_for(chain):
    """Return the default auth_method label for ``chain``."""
    return "evm_xchain" if chain == "evm" else "algorand_wallet"


def link_address(profile, *, chain, address, auth_method, authorized):
    """Attach a proven ``address`` to ``profile`` as primary or secondary.

    The first address on an account (none on ``Profile.address`` and no primary
    row) becomes the primary: it is mirrored onto ``Profile.address`` and
    authorized, preserving today's behaviour. Every later address becomes a
    non-privileged, login-disabled secondary, subject to the per-account cap.
    Re-linking an address the profile already holds is idempotent.

    :param profile: the authenticated user's profile
    :type profile: core.models.Profile
    :param chain: chain identifier of the proven address
    :type chain: str
    :param address: the address the signature proved control of
    :type address: str
    :param auth_method: verification method to record
    :type auth_method: str
    :param authorized: proof token (the consumed nonce)
    :type authorized: str
    :var canonical: canonical dedup form of ``address``
    :type canonical: str
    :var existing: any row already holding ``canonical``
    :type existing: walletauth.models.LinkedAddress | None
    :raises AddressAlreadyLinked: ``canonical`` belongs to another profile
    :raises SecondaryLimitReached: the account is at its secondary cap
    :return: the created/updated row, whether it is primary, permission pending
    :rtype: LinkResult
    """
    canonical = canonical_for(chain, address)
    existing = LinkedAddress.objects.filter(canonical_address=canonical).first()
    if existing and existing.profile_id != profile.id:
        raise AddressAlreadyLinked("This address is already linked to another account")

    # Idempotent re-link of an address this profile already holds.
    if existing is not None:
        existing.authorized = authorized
        existing.verified_at = timezone.now()
        existing.save(update_fields=["authorized", "verified_at"])
        return LinkResult(existing, existing.is_primary, False)

    has_primary = (
        bool(profile.address)
        or LinkedAddress.objects.filter(profile=profile, is_primary=True).exists()
    )

    if not has_primary:
        # Bootstrap the privilege-bearing primary. Persist the address before
        # update_authorized: Profile.save() clears `authorized` on an address
        # change, so authorizing afterwards keeps the stamp intact.
        profile.address = address
        profile.save()
        refreshed = profile.update_authorized(authorized, method=auth_method)
        row = LinkedAddress.objects.create(
            profile=profile,
            address=address,
            canonical_address=canonical,
            chain=chain,
            auth_method=auth_method,
            authorized=authorized,
            is_primary=True,
            login_enabled=True,
        )
        return LinkResult(row, True, not refreshed)

    if LinkedAddress.at_secondary_capacity(profile):
        raise SecondaryLimitReached("Maximum number of connected addresses reached")
    row = LinkedAddress.objects.create(
        profile=profile,
        address=address,
        canonical_address=canonical,
        chain=chain,
        auth_method=auth_method,
        authorized=authorized,
        is_primary=False,
        login_enabled=False,
    )
    return LinkResult(row, False, False)


def sync_primary_linked(profile):
    """Reconcile ``profile``'s primary registry row with ``Profile.address``.

    Called after the authorize flow stamps ``Profile.address``: creates or
    refreshes the single ``is_primary`` row for the current address, drops any
    stale primary row for a previous address, and refuses an address already
    held by another account.

    :param profile: the authenticated user's profile
    :type profile: core.models.Profile
    :var canonical: canonical form of the current primary address
    :type canonical: str
    :var existing: any row already holding ``canonical``
    :type existing: walletauth.models.LinkedAddress | None
    :raises AddressAlreadyLinked: ``canonical`` belongs to another profile
    :return: the primary row, or None when the profile has no address
    :rtype: walletauth.models.LinkedAddress | None
    """
    address = profile.address
    if not address:
        return None
    chain = _chain_of(address)
    canonical = canonical_for(chain, address)

    existing = LinkedAddress.objects.filter(canonical_address=canonical).first()
    if existing and existing.profile_id != profile.id:
        raise AddressAlreadyLinked("This address is already linked to another account")

    # Remove a primary that pointed at a now-replaced address.
    LinkedAddress.objects.filter(profile=profile, is_primary=True).exclude(
        canonical_address=canonical
    ).delete()

    if existing is not None:
        existing.is_primary = True
        existing.login_enabled = True
        existing.authorized = profile.authorized or ""
        existing.verified_at = timezone.now()
        existing.save(
            update_fields=[
                "is_primary",
                "login_enabled",
                "authorized",
                "verified_at",
            ]
        )
        return existing

    return LinkedAddress.objects.create(
        profile=profile,
        address=address,
        canonical_address=canonical,
        chain=chain,
        auth_method=profile.auth_method or _auth_method_for(chain),
        authorized=profile.authorized or "",
        is_primary=True,
        login_enabled=True,
    )
