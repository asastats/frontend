"""Module containing functions for Algorand Name Service (ANS)."""

import logging

from nameservice.anssdk.resolver import AnsResolver
from utils.constants.nameservice import ANS_SUFFIX

logger = logging.getLogger(__name__)


def check_name(name, algod_client):
    """Return provided address or its ANS owner.

    :param name: ANS name or Algorand address
    :type name: str
    :param algod_client: Algorand node client instance
    :type algod_client: :class:`AlgodClient`
    :var algo_name: base name with truncated eventual /ans suffix
    :type algo_name: str
    :var ans_client: ANS resolver client
    :type ans_client: :class:`AnsResolver`
    :var name_info: retrieved ANS entry data
    :type name_info: dict
    :return: str
    """
    algo_name = name.lower().replace(ANS_SUFFIX, "")
    if algo_name.endswith(".algo"):
        ans_client = AnsResolver(algod_client)
        try:
            name_info = ans_client.resolve_name(algo_name)
            if name_info.get("found"):
                return name_info.get("owner")
        except Exception:
            pass

    return name
