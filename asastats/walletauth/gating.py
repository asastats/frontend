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
