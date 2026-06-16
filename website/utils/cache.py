"""Module containing functions for retrieving and setting cache values."""


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
