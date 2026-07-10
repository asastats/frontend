"""drf-spectacular preprocessing hook for the walletauth app."""


def exclude_wallet_endpoints(endpoints, **kwargs):
    """Return ``endpoints`` without the internal ``/api/v2/wallet/`` routes.

    :param endpoints: list of ``(path, path_regex, method, callback)`` tuples
    :type endpoints: list
    :return: filtered list
    :rtype: list
    """
    return [
        (path, path_regex, method, callback)
        for (path, path_regex, method, callback) in endpoints
        if not path.startswith("/api/v2/wallet/")
    ]
