"""Address canonicalization and limits for multi-address accounts.

A user account holds one privilege-bearing *primary* address plus any number of
*secondary* addresses used only for login (opt-in) and action-gating (e.g. a
Swap button). Secondaries confer no permission, subscription, or governance
weight -- those derive solely from the primary (``Profile.address``), exactly as
before this feature.

To guarantee that a single on-chain account cannot be claimed by two profiles --
including via an EVM address and the Algorand xChain (lsig) account it
deterministically controls -- every linked address is deduplicated on a
*canonical* form rather than its raw string.
"""

import logging

from django.conf import settings

from nameservice.xchain import check_evm_address
from utils.clients import algod_instance

logger = logging.getLogger(__name__)

#: Default maximum number of *secondary* (non-primary) addresses per account.
#: Modest by design: cheap insurance against enumeration/abuse and index bloat.
#: Override with ``settings.MAX_SECONDARY_ADDRESSES``.
MAX_SECONDARY_ADDRESSES = 10


class CanonicalizationError(Exception):
    """Raised when an address cannot be reduced to its canonical form."""


def max_secondary_addresses():
    """Return the configured cap on secondary addresses per account.

    :return: the cap, from ``settings.MAX_SECONDARY_ADDRESSES`` or the default
    :rtype: int
    """
    return getattr(settings, "MAX_SECONDARY_ADDRESSES", MAX_SECONDARY_ADDRESSES)


def canonical_for(chain, address):
    """Return the canonical, dedup form of ``address`` on ``chain``.

    Native Algorand addresses are already canonical and returned unchanged. EVM
    addresses are reduced to their deterministic Algorand xChain (lsig)
    counterpart, so an EVM address and its lsig collapse to a single identity
    and cannot be claimed as two.

    :param chain: chain identifier (``"algorand"`` or ``"evm"``)
    :type chain: str
    :param address: stored/display address
    :type address: str
    :var canonical: the lsig counterpart returned by ``check_evm_address``
    :type canonical: str
    :raises CanonicalizationError: when an EVM address cannot be reduced (e.g.
        algod is unreachable), so a non-canonical value is never persisted
    :return: canonical address used as the global uniqueness key
    :rtype: str
    """
    if chain != "evm":
        return address
    canonical = check_evm_address(address, algod_instance())
    # check_evm_address returns its input unchanged on compile/algod failure; a
    # real lsig counterpart is a base32 Algorand address (never 0x-prefixed).
    if not canonical or canonical.lower().startswith("0x"):
        raise CanonicalizationError(
            "Could not derive the Algorand counterpart for the EVM address"
        )
    return canonical
