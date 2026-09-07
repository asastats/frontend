"""Self-scoped "is this address connected to me?" checks for the swap gate.

The engine shows a Swap button next to a browsed address only when that address
is connected to the *current* user. This is a visibility hint, never an
authorization: the swap itself is signed live by the wallet, so a stale link can
at worst surface a button whose signature then fails -- never a loss.

Matching is on canonical identity. An address connected as an EVM wallet matches
its Algorand lsig counterpart (its stored ``canonical_address``) and vice versa,
so browsing either form resolves to the same connection. No canonicalization
(and so no algod) happens here: the browsed value is compared directly against
each row's stored ``address`` and ``canonical_address``. Lookups are strictly
limited to the requesting user's own rows -- never an oracle for whether an
address belongs to anyone else, and independent of ``login_enabled`` (a
connection gates the button whether or not it can also sign in).
"""

import logging

from walletauth.models import LinkedAddress

logger = logging.getLogger(__name__)

#: Length of an Algorand base32 address, which an EVM ``0x…`` value is not.
ALGORAND_ADDRESS_LEN = 58


def _normalized(address):
    """Return the address in comparison form (EVM is case-folded)."""
    return address.lower() if address.lower().startswith("0x") else address


def linked_addresses_for_user(user, addresses):
    """Return the subset of ``addresses`` connected to ``user`` (self-scoped).

    Resolved in a single query against the user's own rows; the returned values
    are the originals as supplied (so the caller can map results back).

    :param user: the requesting user (anonymous yields an empty result)
    :type user: django.contrib.auth.models.User
    :param addresses: browsed addresses to test
    :type addresses: collections.abc.Iterable[str]
    :var owned: the user's stored address and canonical values
    :type owned: set[str]
    :return: the supplied addresses that are connected to ``user``
    :rtype: set[str]
    """
    if not getattr(user, "is_authenticated", False):
        return set()

    by_norm = {}
    for original in addresses:
        if original:
            by_norm.setdefault(_normalized(original), set()).add(original)
    if not by_norm:
        return set()

    owned = set()
    for stored, canonical in LinkedAddress.objects.filter(
        profile__user=user
    ).values_list("address", "canonical_address"):
        owned.add(stored)
        owned.add(canonical)

    matched = set()
    for norm, originals in by_norm.items():
        if norm in owned:
            matched |= originals

    return matched


def algorand_addresses_for_user(user):
    """Return every Algorand address connected to ``user``.

    Unlike :func:`linked_addresses_for_user` this takes no candidate list: the
    caller is not asking "is this one mine" but "what do I hold, everywhere",
    which is the question the router's fee tier is judged on -- the published
    scale counts ASASTATS summed across every linked address, not the address
    being swapped from.

    **Canonical values, deliberately.** ``canonical_address`` is the Algorand
    address in both cases: itself for a native connection, the lsig counterpart
    for an EVM one. So an EVM wallet contributes the account that actually holds
    assets on Algorand, and the caller never has to know which kind of
    connection produced a row.

    Anonymous users hold nothing here: an empty set, and the caller's tier is
    zero. That is correct rather than merely safe -- a discount is a property of
    a profile, and there is no profile.

    :param user: the requesting user (anonymous yields an empty result)
    :type user: django.contrib.auth.models.User
    :return: the user's connected Algorand addresses
    :rtype: set[str]
    """
    if not getattr(user, "is_authenticated", False):
        return set()

    return {
        canonical
        for canonical in LinkedAddress.objects.filter(
            profile__user=user
        ).values_list("canonical_address", flat=True)
        if canonical and len(canonical) == ALGORAND_ADDRESS_LEN
    }


def is_linked_to_user(user, address):
    """Return whether ``address`` is connected to ``user`` (self-scoped).

    :param user: the requesting user
    :type user: django.contrib.auth.models.User
    :param address: the browsed address
    :type address: str
    :return: True when the address is one of the user's connected addresses
    :rtype: bool
    """
    return bool(address) and bool(linked_addresses_for_user(user, [address]))
