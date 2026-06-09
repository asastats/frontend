"""Algorand and cache client factories, configured from settings/env."""

import time

from algosdk.v2client import algod, indexer
from django.conf import settings
from redis import Redis


def algod_instance():
    """Create and return an Algorand algod client configured from settings.

    :return: :class:`algosdk.v2client.algod.AlgodClient`
    """
    return algod.AlgodClient(settings.ALGOD_TOKEN, settings.ALGOD_URL)


def indexer_instance():
    """Create and return an Algorand indexer client configured from settings.

    :return: :class:`algosdk.v2client.indexer.IndexerClient`
    """
    return indexer.IndexerClient(settings.INDEXER_TOKEN, settings.INDEXER_URL)


def redis_instance(replica=False):
    """Return Redis client instance.

    :param replica: should client instantiate replica cache or not
    :type replica: Boolean
    :return: :class:`Redis`
    """
    return Redis(
        host=settings.REDIS_HOST if replica else settings.REDIS_PRIMARY_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_AUTH,
    )


def search_transactions(params, indexer_client=None, delay=0.05, limit=1000):
    """Run a paginated indexer transaction search on the public indexer.

    :param params: indexer search_transactions kwargs (e.g. {"address": ...})
    :type params: dict
    :param indexer_client: optional client; created from settings if omitted
    :type indexer_client: :class:`algosdk.v2client.indexer.IndexerClient`
    :param delay: seconds to sleep between page requests
    :type delay: float
    :param limit: maximum number of transactions requested per page
    :type limit: int
    :var client: indexer client used for the lookup
    :type client: :class:`algosdk.v2client.indexer.IndexerClient`
    :var results: accumulated transaction dicts across pages
    :type results: list
    :var next_token: pagination token for the next page, empty when exhausted
    :type next_token: str
    :var page: single page of indexer results
    :type page: dict
    :return: list of transaction dicts
    """
    client = indexer_client or indexer_instance()
    results, next_token = [], ""
    while True:
        page = client.search_transactions(**params, limit=limit, next_page=next_token)
        results.extend(page.get("transactions", []))
        next_token = page.get("next-token")
        if not next_token:
            return results
        time.sleep(delay)
