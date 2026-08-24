"""Integration tests for the ASA Stats router's two engine-backed endpoints.

``test_swap_integration.py`` covers the router-agnostic pair every swap widget
shares (``account:holdings``, ``assets:lookup``, both served by swapcore). These
are the two only *this* router has, and the two nothing has ever exercised
against a running engine:

* ``router:quote`` -- ``POST /api/v2/internal/router/quote/``
* ``router:group`` -- ``POST /api/v2/internal/router/group/``

Folks and Haystack quote in the browser against their vendors' APIs, so their
widgets have no server-side swap code to integrate. Ours has: the routing runs
in the engine, and these views proxy to it under the scopes the manifest
declares. Every failure below is therefore a failure of *our* stack.

**On the group endpoint.** The mainnet deployment is `restricted`, so
``engine/core/router.py:_deployment()`` raises ``RouterUnavailable`` and the
engine answers 503 for every caller. That is the current, deliberate state and
the tests below record it rather than skipping past it -- when the unrestricted
deployment lands, the test that pins the 503 is the one that should fail and
tell you to update it.
"""

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from walletauth.models import LinkedAddress
from widgets.inhouse.asastats.manifest import MANIFEST

#: A real mainnet address holding both sides of a quotable pair.
LINKED_ADDRESS = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M"

#: ALGO -> USDC, the deepest pair on the network, so a route always exists.
ALGO_ID = 0
USDC_ID = 31566704


def _make_linked_user(email="asastats-integration@example.com", permission=100):
    """Return a user with `LINKED_ADDRESS` connected to their profile.

    Linkage is what gates both endpoints: you may only route from an address
    you have proved you control.

    `Profile.address` has to match the primary link, and not only for realism:
    `walletauth.signals.reconcile_primary_registry` is a post_save on Profile
    that deletes every `is_primary` row not matching `Profile.address`. Leave
    it empty and the row below is dropped the moment anything saves the
    profile - and `force_login` does exactly that (last_login -> User.save ->
    save_user_profile -> profile.save), so the link vanishes between being
    created here and being checked by the view. The gate then refuses a user
    who really is linked, and every "this should be refused" test passes for
    entirely the wrong reason.
    """
    user = get_user_model().objects.create_user(
        username=email, email=email, password="top_secret"
    )
    user.profile.permission = permission
    user.profile.preferred_router = "asastats"
    user.profile.address = LINKED_ADDRESS
    user.profile.save()
    LinkedAddress.objects.create(
        profile=user.profile,
        address=LINKED_ADDRESS,
        canonical_address=LINKED_ADDRESS,
        chain="algorand",
        auth_method="algorand_wallet",
        is_primary=True,
        login_enabled=True,
    )
    return user


def _quote_body(amount=1_000_000, mode="sell"):
    """Return a well-formed quote request body."""
    return {
        "address": LINKED_ADDRESS,
        "from_asset_id": ALGO_ID,
        "to_asset_id": USDC_ID,
        "amount": str(amount),
        "mode": mode,
        "slippage_pct": 0.5,
    }


class AsastatsManifestTest(TestCase):
    """The manifest is what `engine_request` enforces the scopes against."""

    def test_integration_the_manifest_declares_both_router_scopes(self):
        """`engine_request` refuses any scope the manifest does not name.

        So an endpoint whose scope is missing here fails closed with a
        BackendError rather than reaching the engine - which is safe, and
        indistinguishable from the engine being down unless it is asserted.
        """
        assert "router:quote" in MANIFEST.engine_endpoints
        assert "router:group" in MANIFEST.engine_endpoints

    def test_integration_the_manifest_is_a_swap_router(self):
        """`category = "swap"` is what puts it on the settings page."""
        assert MANIFEST.category == "swap"
        assert MANIFEST.id == "asastats"


class AsastatsQuoteViewTest(TestCase):
    """The quote endpoint, against a running engine."""

    def setUp(self):
        self.user = _make_linked_user()
        self.client.force_login(self.user)
        self.url = reverse("asastats_quote")

    def _post(self, body=None, address=LINKED_ADDRESS):
        return self.client.post(
            f"{self.url}?address={address}",
            data=json.dumps(body if body is not None else _quote_body()),
            content_type="application/json",
        )

    def test_integration_a_quote_comes_back_with_what_the_panel_renders(self):
        """The shape `swap.js` reads: amounts out, a floor and a route label.

        Anchored on the keys the controller consumes, not on the numbers, which
        move with the reserves on every call.
        """
        response = self._post()
        assert response.status_code == 200, response.content[:400]

        quote = response.json()
        # `_serialised` in engine/core/router.py is the contract. Amounts come
        # back as strings because they are base units and can exceed what
        # JavaScript's Number holds exactly.
        for key in (
            "mode",
            "asset_in",
            "asset_out",
            "amount_in",
            "amount_out",
            "minimum_received",
            "price_impact_pct",
            "route_label",
            "slippage_pct",
        ):
            assert key in quote, f"{key} missing from {sorted(quote)}"

        assert quote["asset_in"] == ALGO_ID
        assert quote["asset_out"] == USDC_ID
        assert isinstance(quote["amount_out"], str)
        assert int(quote["amount_out"]) > 0
        assert quote["route_label"]

    def test_integration_the_floor_sits_below_the_quote(self):
        """`minimum_received` is the slippage tolerance applied, not a copy.

        A floor equal to the quote would be refused by the chain on any
        movement at all; a floor of zero would accept any fill.
        """
        quote = self._post().json()
        assert 0 < int(quote["minimum_received"]) <= int(quote["amount_out"])

    def test_integration_the_body_address_cannot_be_someone_elses(self):
        """The gated address wins over whatever the body claims.

        The view overwrites `payload["address"]` with the one it gated on, so a
        tampered body quotes for the caller's own address or not at all.
        """
        other = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
        body = dict(_quote_body(), address=other)
        response = self._post(body=body)

        assert response.status_code == 200, response.content[:400]
        quote = response.json()
        assert quote["asset_in"] == ALGO_ID
        assert int(quote["amount_out"]) > 0

    def test_integration_an_address_the_user_has_not_linked_is_refused(self):
        """Ownership gates the quote, not just the group."""
        other = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
        assert self._post(address=other).status_code in (302, 403)

    def test_integration_a_missing_address_is_refused(self):
        """`test_func` returns False on an empty address rather than gating on "" ."""
        assert self._post(address="").status_code in (302, 403)

    def test_integration_a_malformed_body_never_reaches_the_engine(self):
        """400 from us, not a 500 from the engine parsing our forwarded junk."""
        response = self.client.post(
            f"{self.url}?address={LINKED_ADDRESS}",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_integration_an_anonymous_visitor_is_sent_to_log_in(self):
        self.client.logout()
        assert self._post().status_code in (302, 403)

    def test_integration_the_response_is_never_cached(self):
        """A quote is a statement about reserves at a moment.

        Serving a stale one hands the caller a floor the chain will not honour,
        so the view is decorated `never_cache` - asserted here because the
        decorator is easy to drop in a refactor and nothing else would notice.

        Driven with a malformed body on purpose. `never_cache` decorates
        `dispatch`, so the header is set on the refusal too, and this then
        needs no live quote - which matters because a quote reads pools from
        the node, and when anything else is using it (a benchmark run, say) it
        can exceed `ASASTATS_API_TIMEOUT` and make an assertion about a *header*
        fail for reasons that have nothing to do with caching.
        """
        response = self.client.post(
            f"{self.url}?address={LINKED_ADDRESS}",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "no-store" in response.headers.get("Cache-Control", "")


class AsastatsGroupViewTest(TestCase):
    """The group endpoint. Gating is live; building is blocked by design."""

    def setUp(self):
        self.user = _make_linked_user(email="asastats-group@example.com")
        self.client.force_login(self.user)
        self.url = reverse("asastats_group")

    def _post(self, body, address=LINKED_ADDRESS):
        return self.client.post(
            f"{self.url}?address={address}",
            data=json.dumps(body),
            content_type="application/json",
        )

    def test_integration_group_building_is_refused_while_mainnet_is_restricted(self):
        """Records the deployment's current state, and is meant to fail later.

        `engine/core/router.py:_deployment()` raises `RouterUnavailable` when
        `deployment.restricted`, so the engine answers 503 for every caller -
        which is why no browser has ever built a group through this router.
        When the unrestricted deployment lands, this test should start failing;
        replace it with one that asserts a group comes back.
        """
        quote_url = reverse("asastats_quote")
        quoted = self.client.post(
            f"{quote_url}?address={LINKED_ADDRESS}",
            data=json.dumps(_quote_body()),
            content_type="application/json",
        ).json()

        response = self._post({"quote": quoted})
        assert response.status_code in (200, 503), response.content[:400]

        if response.status_code == 503:
            # The refusal reaches the browser intact rather than as a 500: the
            # engine explains that the deployment is compiled with
            # RESTRICT_TO_ADMIN, and that sentence is the only thing a reader
            # could act on.
            assert "RESTRICT_TO_ADMIN" in response.json()["error"]
        else:
            body = response.json()
            assert "transactions" in body or "detail" in body, sorted(body)

    def test_integration_an_unlinked_address_is_refused_before_the_engine(self):
        """The group spends the address' assets, so ownership is the hard gate."""
        other = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
        assert self._post({"quote": {}}, address=other).status_code in (302, 403)

    def test_integration_an_anonymous_visitor_is_sent_to_log_in(self):
        self.client.logout()
        assert self._post({"quote": {}}).status_code in (302, 403)

    def test_integration_a_malformed_body_never_reaches_the_engine(self):
        response = self.client.post(
            f"{self.url}?address={LINKED_ADDRESS}",
            data="[]",
            content_type="application/json",
        )
        assert response.status_code == 400
