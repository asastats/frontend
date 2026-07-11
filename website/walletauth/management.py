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

from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from walletauth.models import LinkedAddress, WalletNonce
from walletauth.verifiers import VERIFIERS, NotSupported

logger = logging.getLogger(__name__)


class CannotRemovePrimary(Exception):
    """Raised when removal targets the primary address."""


class CannotDisablePrimaryLogin(Exception):
    """Raised when login is disabled on the primary address."""


def _current_primary(profile):
    """Return the profile's primary :class:`LinkedAddress`, or ``None``.

    :param profile: the account profile
    :return: the primary row or ``None``
    :rtype: walletauth.models.LinkedAddress | None
    """
    return profile.linked_addresses.filter(is_primary=True).first()


def _normalized(chain, address):
    """Return ``address`` in comparison form (EVM is case-folded).

    :param chain: chain identifier
    :type chain: str
    :param address: address to normalize
    :type address: str
    :rtype: str
    """
    return address.lower() if chain == "evm" else address


def is_bootstrap_promotion(profile, target):
    """Whether ``target`` may become primary / login-enabled without step-up.

    Step-up exists to stop a stolen session escalating against an *existing*
    primary; it cannot be satisfied before any primary exists. That strands
    accounts whose legacy ``Profile.address`` predates the linked-address
    registry: linking that same address creates a non-primary row (because
    ``Profile.address`` is already set in :func:`link_address`), yet there is no
    primary to sign with.

    Bootstrapping is allowed only when BOTH hold, so a stolen session cannot
    promote an attacker's freshly linked wallet:

    * the account has no current primary, and
    * ``target`` is the address already authorized on the profile
      (``Profile.address``) -- an address the account has already proven.

    :param profile: the owning profile
    :type profile: core.models.Profile
    :param target: the row being promoted
    :type target: walletauth.models.LinkedAddress
    :rtype: bool
    """
    if _current_primary(profile) is not None:
        return False
    profile_address = profile.address or ""
    if not profile_address:
        return False
    return _normalized(target.chain, target.address) == _normalized(
        target.chain, profile_address
    )


def verify_step_up(*, user, operation, target_id, nonce, payload):
    """Verify a fresh, operation-bound signature from ``user``'s current primary.

    The signed challenge is ``prefix + "{nonce}:{operation}:{target_id}"``, so a
    signature minted to approve one change cannot be replayed to authorize a
    different one: altering the operation or the target alters the message the
    signature must cover, and recovery fails. The nonce is additionally bound to
    the primary address and single-use (claimed atomically here).

    Framework-agnostic so both the htmx view and any other caller can use it.

    :param user: the authenticated user
    :param operation: the step-up operation ("set_primary" or "set_login")
    :type operation: str
    :param target_id: id of the caller's own row the operation acts on
    :type target_id: int
    :param nonce: the raw server-issued nonce token (not the bound form)
    :type nonce: str
    :param payload: proof fields -- ``signature`` (EVM) or ``signedTransaction``
        (Algorand)
    :type payload: collections.abc.Mapping
    :return: ``None`` on success, else a human-readable error message
    :rtype: str | None
    """
    primary = _current_primary(user.profile)
    if primary is None:
        return "No primary address"
    if not nonce:
        return "Missing step-up signature"
    verifier = VERIFIERS.get(primary.chain)
    if verifier is None:
        return "Unsupported chain"
    bound = f"{nonce}:{operation}:{int(target_id)}"
    try:
        proven = verifier.recover(
            nonce=bound, prefix=WALLET_CONNECT_NONCE_PREFIX, payload=payload
        )
    except NotSupported as exc:
        return str(exc)
    if not proven or _normalized(primary.chain, proven) != _normalized(
        primary.chain, primary.address
    ):
        return "Step-up signature did not match your primary address"
    try:
        nonce_obj = WalletNonce.objects.get(
            nonce=nonce,
            address=primary.address,
            user=user,
            chain=primary.chain,
            used=False,
        )
    except WalletNonce.DoesNotExist:
        return "Step-up challenge not found or already used"
    if nonce_obj.is_expired() or not nonce_obj.claim():
        return "Step-up challenge expired or already used"
    return None


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
    :return: whether the permission refresh succeeded (False -> pending)
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
    logger.info("walletauth: primary changed (permission_pending=%s)", not refreshed)
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
