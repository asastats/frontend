"""Module containing functions for retrieving and setting cache values."""

from utils.constants.core import LIVEREFRESH_HOLDINGS_KEY


# # BUNDLE
def cached_bundle(bundle, cache_client):
    """Return addresses associated with provided bundle from cache.

    :param bundle: hash value associated with target addresses
    :type bundle: str
    :param cache_client: Redis client instance
    :type cache_client: :class:`Redis`
    :var value: cached value
    :type value: bytes
    :return: str
    """
    value = cache_client.get(bundle)
    if value is not None:
        try:
            return value.decode("ascii")
        except ValueError:
            pass

    return False


def cupdate_bundle(bundle, addresses, cache_client):
    """Update cache with bundle named tuple.

    :param bundle: hash made from provided addresses
    :type bundle: str
    :param addresses: Algorand addresses separated by spaces
    :type addresses: string
    :param cache_client: Redis client instance
    :type cache_client: :class:`Redis`
    """
    cache_client.set(bundle, addresses)


# # LIVE REFRESH
def cached_live_holdings(page, cache_client):
    """Return the engine's fingerprint of what `page` holds, or an empty string.

    **What the account holds, not what those holdings are worth.** The live
    pass re-prices a watched page every block, and the figures it publishes are
    swapped into the reader's page out of band. That can only ever reach an
    element the page already has -- so an asset just bought has no row to land
    in, one just sold is never mentioned and its stale row simply stays, and an
    amount column is not what a value fragment carries. A change to this is
    therefore not a fragment; it is a reload, and this is the one fact both
    services agree on.

    It keys the rendered address page for the same reason. Without that, the
    reload the widget orders would be answered out of a ``cache_page`` entry
    built before the holdings changed, and the reader would be sent round a
    loop to be shown the same stale rows again.

    An empty string when the engine has never read this page -- which is every
    page nobody watches -- and that is a value, not a failure: it keys those
    pages exactly as they were keyed before any of this existed.

    :param page: the page's key, an address or an uppercase bundle hash
    :type page: str
    :param cache_client: Redis client instance
    :type cache_client: :class:`Redis`
    :return: str
    """
    value = cache_client.hget(LIVEREFRESH_HOLDINGS_KEY, page)
    if isinstance(value, bytes):
        return value.decode("ascii", "replace")
    return value or ""
