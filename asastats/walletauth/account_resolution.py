"""Resolve a Django account from a *proven* wallet address.

A verified on-chain address is matched verbatim against the :class:`LinkedAddress`
registry, so resolution is chain-agnostic: an Algorand wallet stores its base32
address, an EVM/xChain wallet stores its ``0x`` address. The Algorand counterpart
of an EVM address is **not** computed here -- matching is on the stored address,
which keeps login off the algod ``/compile`` path. (Canonical uniqueness makes
the stored address effectively unique, so this is unambiguous.)

Only addresses a user opted in for sign-in resolve to an account: the primary is
always login-capable, while secondaries must have ``login_enabled`` set. Every
registry row was proven by a signature when it was created, so sign-in never
creates accounts and never trusts an address the client merely names.
"""

import logging

from walletauth.models import LinkedAddress

logger = logging.getLogger(__name__)


class AmbiguousWalletAddress(Exception):
    """Raised when more than one account has the same address login-enabled.

    This is a data-integrity condition the canonical unique constraint is meant
    to prevent. Surfacing it (rather than collapsing to "not linked") lets the
    sign-in view tell the user precisely why their wallet was refused.
    """


def _resolve_by_address(address):
    """Return the user who may sign in with ``address``, or ``None``.

    The stored address is matched exactly against a login-enabled registry row,
    so the same lookup serves every chain. For EVM the proven address is the
    ``0x`` address, stored as-is.

    :param address: proven address, in the chain's own namespace
    :type address: str
    :var linked: the single login-enabled row holding ``address``, if any
    :type linked: walletauth.models.LinkedAddress
    :raises AmbiguousWalletAddress: when more than one row login-enables ``address``
    :return: the owning user, or None when unlinked/not login-enabled
    :rtype: django.contrib.auth.models.User | None
    """
    try:
        linked = LinkedAddress.objects.select_related("profile__user").get(
            address=address, login_enabled=True
        )
    except LinkedAddress.DoesNotExist:
        return None
    except LinkedAddress.MultipleObjectsReturned:
        # More than one account login-enables this address. Refuse and say so,
        # rather than guessing. The canonical unique constraint prevents ever
        # reaching here.
        logger.warning("walletauth: multiple login-enabled rows for a wallet address")
        raise AmbiguousWalletAddress
    return linked.profile.user


#: Account resolvers keyed by request chain. Both chains resolve by the stored
#: address; EVM does not need its Algorand counterpart to authenticate.
ACCOUNT_RESOLVERS = {
    "algorand": _resolve_by_address,
    "evm": _resolve_by_address,
}


def resolve_account(chain, address):
    """Resolve the account that may sign in with ``address`` on ``chain``.

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
