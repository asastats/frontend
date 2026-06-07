"""HTTP client for the ASA Stats backend (replaces in-process engine calls).

Every function here calls the closed backend over HTTP, authenticating with this
deployment's credential (``ASASTATS_API_KEY``). This is the only seam between the
open app and the proprietary engine.
"""

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
