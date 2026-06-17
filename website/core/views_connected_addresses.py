"""Server-rendered (htmx) connected-addresses management for the site's core app.

There are three views:

* :func:`profile_addresses` -- the full page (GET); renders the address list
  inline via the ``address_list`` partial in ``profile_addresses.html``.
* :func:`profile_addresses_action` -- the htmx endpoint (POST); performs one
  operation and returns the refreshed ``#address_list`` partial.
* :func:`profile_link_address` -- the "link another wallet" page (GET).

The security model entirely server-side: privilege-expanding operations
(``set_primary``, enabling login) require a fresh, operation-bound signature from
the *current primary*, verified by :func:`walletauth.management.verify_step_up`;
reducing operations (disable login, remove) need only the authenticated session.
The view -- never the client -- decides whether step-up is required, from the
operation semantics. Targets are resolved strictly within the caller's own rows,
so there is no ownership oracle.
"""

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from utils.constants.core import ALGORAND_WALLETS
from walletauth.management import (
    CannotDisablePrimaryLogin,
    CannotRemovePrimary,
    remove_address,
    set_login_enabled,
    set_primary,
    verify_step_up,
)
from walletauth.models import LinkedAddress

#: Operations the action endpoint accepts.
_OPERATIONS = {"set_primary", "set_login", "remove"}
#: POST values (from htmx hx-vals / ajax) that count as a truthy "enabled".
_TRUE = {"true", "True", "1", "on"}


def _address_rows(profile):
    """Return the profile's linked addresses as template dicts, primary first.

    :param profile: the account profile
    :return: list of ``{id, address, chain, is_primary, login_enabled, label}``
    :rtype: list[dict]
    """
    return [
        {
            "id": row.id,
            "address": row.address,
            "chain": row.chain,
            "is_primary": row.is_primary,
            "login_enabled": row.login_enabled,
            "label": row.label,
        }
        for row in profile.linked_addresses.order_by("-is_primary", "verified_at")
    ]


def _list_partial(request, *, error=None):
    """Render the ``address_list`` fragment; signal errors via ``HX-Trigger``.

    htmx only swaps 2xx responses, so on error we still return 200 but set
    ``HX-Reswap: none`` (leave the current list untouched) and fire a
    ``wallet-error`` event the page turns into a toast.

    :param request: the authenticated request
    :param error: optional error message to surface to the user
    :type error: str | None
    :rtype: django.http.HttpResponse
    """
    response = render(
        request,
        "profile_addresses.html#address_list",
        {"addresses": _address_rows(request.user.profile)},
    )
    # Per-user content: never let a shared cache or restore leak another's list.
    response["Cache-Control"] = "private, no-store"
    if error is not None:
        response["HX-Reswap"] = "none"
        response["HX-Trigger"] = json.dumps({"wallet-error": error})
    return response


@login_required
def profile_addresses(request):
    """Render the connected-addresses management page (full document).

    :param request: the authenticated request
    :rtype: django.http.HttpResponse
    """
    return render(
        request,
        "profile_addresses.html",
        {
            "addresses": _address_rows(request.user.profile),
            "link_address_url": reverse("profile_link_address"),
            "wallet_connect_project_id": getattr(
                settings, "WALLET_CONNECT_PROJECT_ID", ""
            ),
        },
    )


@login_required
@require_POST
def profile_addresses_action(request):
    """Perform one management operation and return the refreshed list partial.

    :param request: the authenticated request carrying ``operation`` and
        ``target_id`` (plus ``enabled`` for ``set_login`` and a step-up
        ``nonce``/signature for privilege-expanding operations)
    :rtype: django.http.HttpResponse
    """
    operation = request.POST.get("operation")
    if operation not in _OPERATIONS:
        return _list_partial(request, error="Unknown operation")

    profile = request.user.profile
    try:
        target = profile.linked_addresses.get(id=request.POST.get("target_id"))
    except (LinkedAddress.DoesNotExist, ValueError, TypeError):
        # Not found, or not the caller's: identical answer, no ownership oracle.
        return _list_partial(request, error="Address not found")

    enabled = request.POST.get("enabled") in _TRUE
    # The server decides step-up from operation semantics, never the client.
    if operation == "set_primary" or (operation == "set_login" and enabled):
        error = verify_step_up(
            user=request.user,
            operation=operation,
            target_id=target.id,
            nonce=request.POST.get("nonce"),
            payload=request.POST,
        )
        if error is not None:
            return _list_partial(request, error=error)

    try:
        if operation == "set_primary":
            set_primary(profile, target)
        elif operation == "set_login":
            set_login_enabled(profile, target, enabled)
        else:
            remove_address(profile, target)
    except (CannotDisablePrimaryLogin, CannotRemovePrimary) as exc:
        return _list_partial(request, error=str(exc))

    return _list_partial(request)


@login_required
def profile_link_address(request):
    """Render the 'link another wallet' page (reuses the authorize wallet UI).

    :param request: the authenticated request
    :rtype: django.http.HttpResponse
    """
    return render(
        request,
        "profile_link_address.html",
        {
            "wallets": ALGORAND_WALLETS,
            "wallet_connect_project_id": getattr(
                settings, "WALLET_CONNECT_PROJECT_ID", ""
            ),
        },
    )
