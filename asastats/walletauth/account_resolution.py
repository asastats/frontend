"""Resolve a Django account from a *proven* wallet address.

A verified on-chain address is matched verbatim against the address stored on a
profile, so resolution is chain-agnostic: an Algorand wallet stores its base32
address, an EVM/xChain wallet stores its ``0x`` address. The Algorand
counterpart of an EVM address is derived lazily by ``Profile.algorand_address``
when actually needed (display, on-chain use); it is **not** required to
authenticate, which keeps login off the algod ``/compile`` path.

Only addresses that were *linked while authenticated* (the authorize flow, which
sets ``Profile.authorized``) resolve to an account. Sign-in therefore never
creates accounts and never trusts an address the client merely names.
"""

import logging

from core.models import Profile

logger = logging.getLogger(__name__)


class AmbiguousWalletAddress(Exception):
    """Raised when more than one account has the same address verified.

    This is a data-integrity condition the unique constraint in the docs is
    meant to prevent. Surfacing it (rather than collapsing to "not linked")
    lets the sign-in view tell the user precisely why their wallet was refused.
    """


def _resolve_by_address(address):
    """Return the user whose profile has ``address`` verified, or ``None``.

    The stored address is matched exactly, so the same lookup serves every
    chain. For EVM the proven address is the ``0x`` address, stored as-is.

    :param address: proven address, in the chain's own namespace
    :type address: str
    :var profile: the single profile linked to ``address``, if unambiguous
    :type profile: core.models.Profile
    :raises AmbiguousWalletAddress: when more than one profile claims ``address``
    :return: the owning user, or None when unlinked/unverified
    :rtype: django.contrib.auth.models.User | None
    """
    try:
        profile = Profile.objects.select_related("user").get(address=address)
    except Profile.DoesNotExist:
        return None
    except Profile.MultipleObjectsReturned:
        # More than one account claims this address. Refuse and say so, rather
        # than guessing. A unique constraint on the verified address prevents
        # ever reaching here.
        logger.warning("walletauth: multiple profiles for a wallet address")
        raise AmbiguousWalletAddress
    if not profile.authorized:
        # Address is set on the profile but was never proven/linked.
        return None
    return profile.user


#: Account resolvers keyed by request chain. Both chains resolve by the stored
#: address; EVM does not need its Algorand counterpart to authenticate.
ACCOUNT_RESOLVERS = {
    "algorand": _resolve_by_address,
    "evm": _resolve_by_address,
}


def resolve_account(chain, address):
    """Resolve the account linked to ``address`` on ``chain``.

    :param chain: request chain identifier (e.g. ``"algorand"``)
    :type chain: str
    :param address: proven address for that chain
    :type address: str
    :return: the linked user, or None when unsupported/unlinked
    :rtype: django.contrib.auth.models.User | None
    """
    resolver = ACCOUNT_RESOLVERS.get(chain)
    if resolver is None:
        return None
    return resolver(address)
