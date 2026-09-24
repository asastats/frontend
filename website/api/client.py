"""HTTP client for the ASA Stats backend (replaces in-process engine calls).

Every function here calls the closed backend over HTTP, authenticating with this
deployment's credential (``ASASTATS_API_KEY``). This is the only seam between the
open app and the proprietary engine.
"""

from urllib.parse import quote

import requests
from django.conf import settings

from utils.helpers import bundle_from_addresses, canonical_bundle


class BackendError(Exception):
    """Raised when the ASA Stats backend returns a non-success response.

    Carries the backend's own status and decoded detail where there is one, so
    a caller can pass a meaningful refusal through instead of turning it into a
    500. The engine's router endpoints rely on this: a restricted deployment
    answers 503 with an explanation of *why* no group can be built, and that
    sentence is the only thing a reader could act on.
    """

    def __init__(self, message, status_code=None, detail=None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


def _headers():
    return {"Authorization": f"Bearer {settings.ASASTATS_API_KEY}"}


def _request(method, path, **kwargs):
    """Call the backend at `path`, which must be absolute from its root.

    The URL is a plain concatenation, so a caller passing a bare relative path
    silently produces a broken host: ``router/quote/`` became
    ``http://host:8001router/quote/``, which never reached the engine at all.
    The asastats widget shipped with exactly that and could not have worked
    anywhere - nothing caught it because every unit test mocks this function,
    and the malformed URL only surfaces as an InvalidURL from requests.

    Refusing it here is one line and covers every future caller, which is worth
    more than having fixed the one that had it wrong.
    """
    if not path.startswith("/"):
        raise BackendError(
            f"backend path must start with '/', got {path!r} - it is joined to "
            f"{settings.ASASTATS_API_URL!r} by concatenation"
        )

    # **A backend that cannot be reached is a `BackendError` like any other.**
    # A transport failure came out of `requests` as its own exception and went
    # past every caller's `except BackendError`. Wrapped here because this is
    # the one place that knows the request was ours, and because the
    # alternative is every caller naming a `requests` type to catch a condition
    # the client is supposed to hide. `status_code` stays None: there was no
    # response to have one.
    try:
        resp = requests.request(
            method,
            f"{settings.ASASTATS_API_URL}{path}",
            headers=_headers(),
            timeout=settings.ASASTATS_API_TIMEOUT,
            **kwargs,
        )
    except requests.RequestException as error:
        raise BackendError(f"could not reach the backend: {error}") from error
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail")
        except ValueError:
            detail = None
        raise BackendError(
            f"{resp.status_code}: {resp.text[:200]}",
            status_code=resp.status_code,
            detail=detail,
        )
    return resp


def fetch_account_holdings(address, allowed_scopes):
    """Return a single address' opted-in holdings via the account:holdings scope.

    The backend returns a mapping of asset id to ``{name, unit, decimals, amount}``
    (ALGO is id 0); every key present is, by definition, opted in.

    Defense-in-depth: the only caller already constrains address to \\w{58},
    but encode the path segment so this helper can't be misused to traverse.

    :param address: single Algorand address
    :type address: str
    :param allowed_scopes: the widget manifest's declared engine endpoints
    :type allowed_scopes: list
    :return: dict
    """
    safe = quote(str(address), safe="")
    return engine_request(
        "account:holdings",
        "GET",
        f"/api/v2/internal/accounts/{safe}/holdings",
        allowed_scopes,
    ).json()


def fetch_asset_matches(query, allowed_scopes):
    """Return ranked asset metadata matches via the assets:lookup scope.

    :param query: asset id, unit, or name/unit prefix
    :type query: str
    :param allowed_scopes: the widget manifest's declared engine endpoints
    :type allowed_scopes: list
    :return: list
    """
    return engine_request(
        "assets:lookup",
        "GET",
        "/api/v2/internal/assets",
        allowed_scopes,
        params={"q": query},
    ).json()


def fetch_price():
    """Return {"price": <ALGO price in USDC>}."""
    return _request("GET", "/api/v2/price/").json().get("price")


def fetch_serialized_account(value, addresses="", light=False, permission=0):
    """Return serialized_data for a single address or a bundle.

    **Two endpoints, one shape apart.** `light=True` asks
    `internal/accounts/<value>/batched`, whose NFT records drop the listings and
    purchase history that only an opened collection shows and carry a
    `floor_price` scalar in place of the floor listings. Everything else - the
    totals, the asset rows, every collection and every item - is identical, so
    only the parts of this app that render an opened NFT care which one they
    got.

    The address page asks for the light one; this app's own JSON API does not,
    because what it serves is the shared contract.

    :param value: single address, or the bundle hash (this app's local id)
    :param addresses: space-joined addresses for multi-address bundles
    :param light: ask for the thinner NFT records
    :type light: bool
    :param permission: the reader's class, for the engine to size admission by
    :type permission: int
    """
    # **Set here, never taken from the browser.** This layer holds the
    # deployment credential and is the only party that knows who the reader is.
    # A value the page could edit would decide nothing.
    params = {"addresses": addresses} if addresses else {}
    if permission:
        params["permission"] = permission
    params = params or None
    path = f"/api/v2/internal/accounts/{value}/"
    if light:
        path = f"/api/v2/internal/accounts/{value}/batched"
    return _request("GET", path, params=params).json()


def fetch_collection_items(value, name, addresses=""):
    """Return one NFT collection whole, items and all.

    What the light payload leaves out - an item's listings and its purchase
    history - for the one collection a reader opened. The engine slices it out
    of the full payload, so these are the same records the shared endpoint
    sends rather than a second construction of them.

    :param value: single address, or the bundle hash (this app's local id)
    :param name: the collection's name, as the payload reports it
    :type name: str
    :param addresses: space-joined addresses for multi-address bundles
    :return: dict
    """
    # **An old bookmark carries an old hash, and the engine re-derives.** It
    # recomputes `bundle_from_addresses` over the addresses supplied and
    # refuses the request when that does not match the hash in the path, so a
    # bundle URL saved before the hash became sort-and-dedupe is re-hashed
    # here. Keyed on a space rather than on length, matching the account path:
    # a single address passes through untouched.
    if " " in addresses:
        value = bundle_from_addresses(addresses)

    params = {"name": name}
    if addresses:
        params["addresses"] = addresses
    return _request(
        "GET", f"/api/v2/internal/accounts/{value}/collection", params=params
    ).json()


def fetch_capabilities():
    """Return this deployment's capabilities, e.g. {"permission": <int>}."""
    return _request("GET", "/api/v2/capabilities/").json()


def start_export(value, addresses):
    """Trigger backend CSV-export processing. `addresses` is authoritative."""
    return _request(
        "POST", "/api/v2/exports/", json={"bundle": value, "addresses": addresses}
    ).json()


def export_status(bundle):
    """Return processing/finished status + report filename for ``bundle``.

    **Canonicalised, because the export is not stored under the hash the
    reader's URL carries.** `ExportView` ignores the `bundle` it is posted and
    keys the export by `_cache_key(addresses)` - the hash recomputed from the
    addresses - while this poll looks the value up verbatim. An old bookmark
    therefore starts an export that runs, completes, and is never found again:
    the status stays `{}`, the download 404s, and nothing anywhere logs an
    error, because an empty status is exactly what "not ready yet" looks like.

    Silent, and it costs a full CSV export every time a reader gives up and
    tries again.
    """
    return _request("GET", f"/api/v2/exports/{canonical_bundle(bundle)}/status/").json()


def download_export(bundle):
    """Return the export archive bytes (streamed) for ``bundle``.

    Canonicalised for the same reason as :func:`export_status`.
    """
    return _request(
        "GET", f"/api/v2/exports/{canonical_bundle(bundle)}/download/", stream=True
    ).content


def reset_export(bundle):
    """Delete the backend export archive and reset its status for ``bundle``.

    Canonicalised for the same reason as :func:`export_status` - and here the
    cost of not doing it is a delete that silently removes nothing, leaving the
    archive the reader asked to be rid of exactly where it was.
    """
    return _request("DELETE", f"/api/v2/exports/{canonical_bundle(bundle)}/").json()


def engine_request(scope, method, path, allowed_scopes, **kwargs):
    """Call a scoped engine endpoint on behalf of a widget.

    The widget builds its own ``path``; this primitive adds the deployment
    credential (via :func:`_request`) and refuses any scope the widget did not
    declare in its manifest ``engine_endpoints``.

    :param scope: engine scope this call requires, e.g. "historic:evaluate"
    :type scope: str
    :param method: HTTP method
    :type method: str
    :param path: engine path beneath the API root
    :type path: str
    :param allowed_scopes: the widget manifest's declared engine endpoints
    :type allowed_scopes: list
    :return: :class:`requests.Response`
    """
    if scope not in allowed_scopes:
        raise BackendError(f"Scope '{scope}' not declared by widget.")

    return _request(method, path, **kwargs)
