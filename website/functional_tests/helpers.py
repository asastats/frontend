"""Module containing helper functions for the website functional tests."""

import logging
import sys
from copy import deepcopy
from random import choice, randint

from utils.clients import indexer_instance
from utils.helpers import pause

from .fixtures import (
    HOLDER_SIZE_TYPES,
    HOLDERS_SIZE_MULTIPLIER,
    INDEXER_FETCH_LIMIT,
    INDEXER_PAGE_DELAY,
    MAJOR_ASSET_IDS,
    OTHER_ASSET_IDS,
)

logger = logging.getLogger(__name__)


def _pick_asset_holder(balances, holder_syze):
    shift = randint(1, len(balances) // 100)
    if holder_syze == 0:
        return balances[shift]
    if holder_syze == 1:
        return balances[len(balances) // 2 - (len(balances) // 100) // 2 + shift]
    return balances[-shift]


def _random_asset(major=True):
    return choice(MAJOR_ASSET_IDS) if major else choice(OTHER_ASSET_IDS)


def _random_holder_size():
    return choice(HOLDER_SIZE_TYPES)


def asset_holder(asset_id=None, holder_size=None):
    if asset_id is None:
        asset_id = _random_asset()
    if holder_size is None:
        holder_size = _random_holder_size()

    indexer_client = indexer_instance()
    return asset_id, *_pick_asset_holder(
        _sorted_asset_holders(asset_id, indexer_client), holder_size
    )


# # INDEXER
def _sorted_asset_holders(asset_id, indexer_client, **kwargs):
    """ """
    delay = kwargs.pop("delay", INDEXER_PAGE_DELAY)
    limit = kwargs.pop("limit", INDEXER_FETCH_LIMIT)
    pause(delay)

    params = {
        "limit": limit,
        "min_balance": 1,
        **kwargs,
    }
    balances = []
    results = _asset_balances(asset_id, params, indexer_client)
    while results.get("balances") and len(balances) < HOLDERS_SIZE_MULTIPLIER * limit:
        balances.extend(results.get("balances"))
        pause(delay)
        results = _asset_balances(
            asset_id, params, indexer_client, next_page=results.get("next-token")
        )

    return sorted(
        [(entry.get("amount"), entry.get("address")) for entry in balances],
        reverse=True,
    )


def _asset_balances(
    asset_id, params, indexer_client, next_page=None, delay=1, error_delay=5, retries=20
):
    """Fetch and return accounts holding provided `asset_id` based on provided params.

    :param asset_id: Algorand Standard Asset
    :type asset_id: int
    :param params: collection of parameters to indexer search method
    :type params: dict
    :param indexer_client: Algorand Indexer client instance
    :type indexer_client: :class:`IndexerClient`
    :param next_page: custom code identifying very next page of search results
    :type next_page: str
    :param delay: delay in seconds before Indexer call
    :type delay: float
    :param error_delay: delay in seconds after error
    :type error_delay: int
    :param retries: maximum number of retries before system exit
    :type retries: int
    :param _params: updated parameters to indexer search method
    :type _params: dict
    :var counter: current number of retries to fetch the block
    :type counter: int
    :return: dict
    """
    _params = deepcopy(params)
    if next_page:
        _params.update({"next_page": next_page})
    counter = 0
    while True:
        try:
            pause(delay)
            return indexer_client.asset_balances(asset_id, **_params)
        except Exception as e:
            if counter >= retries:
                logger.error("Maximum number of retries reached. Exiting...")
                sys.exit()
            logger.error(
                "Exception %s raised searching transactions: %s; Paused..."
                % (
                    e,
                    _params,
                )
            )
            pause(error_delay)
            counter += 1
