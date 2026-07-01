"""HTTP client for the ASA Stats backend (replaces in-process engine calls).

Every function here calls the closed backend over HTTP, authenticating with this
deployment's credential (``ASASTATS_API_KEY``). This is the only seam between the
open app and the proprietary engine.
"""

from urllib.parse import quote

import requests
from django.conf import settings


class BackendError(Exception):
    """Raised when the ASA Stats backend returns a non-success response."""


def _headers():
    return {"Authorization": f"Bearer {settings.ASASTATS_API_KEY}"}


def _request(method, path, **kwargs):
    resp = requests.request(
        method,
        f"{settings.ASASTATS_API_URL}{path}",
        headers=_headers(),
        timeout=settings.ASASTATS_API_TIMEOUT,
        **kwargs,
    )
    if resp.status_code >= 400:
        raise BackendError(f"{resp.status_code}: {resp.text[:200]}")
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


def fetch_serialized_account(value, addresses=""):
    """Return serialized_data for a single address or a bundle.

    :param value: single address, or the bundle hash (this app's local id)
    :param addresses: space-joined addresses for multi-address bundles
    """
    params = {"addresses": addresses} if addresses else None
    return _request("GET", f"/api/v2/internal/accounts/{value}/", params=params).json()


def fetch_capabilities():
    """Return this deployment's capabilities, e.g. {"permission": <int>}."""
    return _request("GET", "/api/v2/capabilities/").json()


def start_export(value, addresses):
    """Trigger backend CSV-export processing. `addresses` is authoritative."""
    return _request(
        "POST", "/api/v2/exports/", json={"bundle": value, "addresses": addresses}
    ).json()


def export_status(bundle):
    """Return processing/finished status + report filename for ``bundle``."""
    return _request("GET", f"/api/v2/exports/{bundle}/status/").json()


def download_export(bundle):
    """Return the export archive bytes (streamed) for ``bundle``."""
    return _request("GET", f"/api/v2/exports/{bundle}/download/", stream=True).content


def reset_export(bundle):
    """Delete the backend export archive and reset its status for ``bundle``."""
    return _request("DELETE", f"/api/v2/exports/{bundle}/").json()


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
