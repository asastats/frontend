"""Module containing public functions for Algorand name services."""

import logging

from nameservice import ans, nfd, xchain
from utils.constants.nameservice import ANS_SUFFIX, NFD_SUFFIX

logger = logging.getLogger(__name__)


def check_name(name, algod_client):
    """Return name service owner for `name` or itself if name isn't registered.

    :param name: ANS name or Algorand address
    :type name: str
    :param algod_client: Algorand node client instance
    :type algod_client: :class:`AlgodClient`
    :var container: temporary container to check if both providers registered name
    :type container: list
    :var result: resolved collection of address(es)
    :type result: list
    :return: str
    """
    if name.lower().endswith(ANS_SUFFIX):
        return ans.check_name(name, algod_client)

    if name.lower().replace(NFD_SUFFIX, "").endswith(".algo"):
        return nfd.check_name(name, algod_client)

    return xchain.check_evm_address(name, algod_client)
