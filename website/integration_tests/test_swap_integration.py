"""Integration tests for the swap widget's two engine-backed endpoints.

The swap panel is the piece of the redesign that has the most behaviour behind
it, and until now nothing exercised the data it runs on. Its jest suite covers
the controller against fixtures, and the functional tests drive the modal in a
browser with the backend mocked -- so both halves are tested against an agreed
*shape*, and nothing checks that the backend still produces it.

Two endpoints reach the engine, both declared as scopes in the widget manifest:

* ``account:holdings`` -- :func:`api.client.fetch_account_holdings`, behind
  ``/widgets/swapcore/<address>/holdings``
* ``assets:lookup`` -- :func:`api.client.fetch_asset_matches`, behind
  ``/widgets/swapcore/assets``

The tests are split by what they can tell you. ``SwapBackendDataTest`` calls
the client directly and is about the backend contract -- the payload shape the
controller's opt-in logic and unit rendering depend on. The view classes cover
delivery and gating, which is where the widget's own code can go wrong without
the backend changing at all.
"""

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from api.client import BackendError, fetch_account_holdings, fetch_asset_matches
from walletauth.models import LinkedAddress
from widgets.inhouse.swapcore.manifest import MANIFEST

#: A real mainnet address with a varied set of opted-in assets.
LINKED_ADDRESS = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M"

#: A query the asset index is certain to answer, and a verified asset at that.
KNOWN_QUERY = "USDC"

#: Keys the panel template and swap.js both rely on for every holding.
HOLDING_KEYS = {"name", "unit", "decimals", "amount"}


def _make_linked_user(email="swap-integration@example.com", permission=100):
    """Return a user with `LINKED_ADDRESS` connected to their profile.

    Linkage is what gates the holdings endpoint: you may only read holdings
    for an address you have proved you control.

    :param email: username and email for the created user
    :type email: str
    :param permission: tier permission integer for the profile
    :type permission: int
    :return: :class:`django.contrib.auth.models.User`
    """
    user = get_user_model().objects.create_user(
        username=email, email=email, password="top_secret"
    )
    user.profile.permission = permission
    # The profile address has to match the primary link, and not only for
    # realism: walletauth.signals.reconcile_primary_registry is a post_save on
    # Profile that deletes every `is_primary` row not matching
    # `Profile.address` -- so with the address left empty, the row below is
    # dropped the moment anything saves the profile. Logging in does exactly
    # that (last_login -> User.save -> save_user_profile -> profile.save), so
    # the link would vanish between being created here and being checked by
    # the view, and the gate would refuse a user who really is linked.
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


class SwapBackendDataTest(TestCase):
    """Testing class for the two engine calls the widget makes."""

    def test_integration_holdings_come_back_keyed_by_asset_id(self):
        """The controller derives opt-in from membership of this mapping.

        Every key present *is* an opted-in asset, so the shape is not
        incidental -- if this came back as a list, or keyed by unit, the panel
        would offer opt-in transactions for assets already held.
        """
        holdings = fetch_account_holdings(LINKED_ADDRESS, MANIFEST.engine_endpoints)

        self.assertIsInstance(
            holdings,
            dict,
            f"holdings came back as {type(holdings).__name__}, not a mapping "
            "of asset id to metadata",
        )
        self.assertTrue(holdings, "no holdings for an address known to hold assets")
        self.assertTrue(
            all(str(key).isdigit() for key in holdings),
            f"holdings keys are not all asset ids: {sorted(holdings)[:5]}",
        )

    def test_integration_every_holding_carries_what_the_panel_needs(self):
        """A missing `decimals` renders every amount off by orders of magnitude."""
        holdings = fetch_account_holdings(LINKED_ADDRESS, MANIFEST.engine_endpoints)

        incomplete = {
            asset_id: sorted(HOLDING_KEYS - set(meta))
            for asset_id, meta in holdings.items()
            if not HOLDING_KEYS.issubset(meta)
        }
        self.assertEqual(
            incomplete,
            {},
            f"holdings missing required keys: {incomplete}. swap.js reads all "
            "four; `decimals` in particular is what converts base units to a "
            "displayed amount.",
        )

    def test_integration_algo_is_present_as_asset_zero(self):
        """ALGO is the default source leg, and it is id 0 by convention."""
        holdings = fetch_account_holdings(LINKED_ADDRESS, MANIFEST.engine_endpoints)

        self.assertIn(
            "0",
            holdings,
            f"ALGO (id 0) is absent from holdings: {sorted(holdings)[:5]}. The "
            "panel opens on ALGO, so it would open on an empty leg.",
        )

    def test_integration_asset_search_returns_ranked_matches(self):
        matches = fetch_asset_matches(KNOWN_QUERY, MANIFEST.engine_endpoints)

        self.assertIsInstance(matches, list, f"got {type(matches).__name__}")
        self.assertTrue(matches, f"no matches for {KNOWN_QUERY!r}")
        first = matches[0]
        for key in ("id", "name", "unit", "decimals"):
            self.assertIn(key, first, f"match is missing {key!r}: {first}")

    def test_integration_an_undeclared_scope_is_refused(self):
        """The manifest is the authority on what a widget may call.

        ``engine_request`` refuses any scope the widget did not declare, which
        is the boundary that keeps one widget from reaching another's data.
        Asserting it here rather than in a unit test means the refusal is
        checked against the real call path.
        """
        with self.assertRaises(BackendError):
            fetch_asset_matches(KNOWN_QUERY, allowed_scopes=[])

        with self.assertRaises(BackendError):
            fetch_account_holdings(LINKED_ADDRESS, allowed_scopes=["assets:lookup"])


class SwapHoldingsViewTest(TestCase):
    """Testing class for the holdings partial and its linkage gate."""

    def setUp(self):
        self.url = reverse("swap_holdings", args=[LINKED_ADDRESS])

    def test_integration_holdings_panel_renders_for_a_linked_user(self):
        self.client.force_login(_make_linked_user())

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "swap/_panel.html")
        self.assertTrue(
            response.context["holdings"],
            "the panel rendered with no holdings, so the source picker is empty",
        )

    def test_integration_holdings_are_flattened_id_sorted_with_algo_first(self):
        """The view turns the mapping into the list the template iterates."""
        self.client.force_login(_make_linked_user())

        holdings = self.client.get(self.url).context["holdings"]

        self.assertEqual(
            holdings[0]["id"],
            0,
            "ALGO is not the first entry, so the panel does not open on it",
        )
        ids = [item["id"] for item in holdings]
        self.assertEqual(ids, sorted(ids), f"holdings are not id-sorted: {ids}")
        self.assertTrue(
            all(isinstance(item["id"], int) for item in holdings),
            "ids reached the template as strings; the controller compares them "
            "numerically",
        )

    def test_integration_the_json_island_matches_the_rendered_holdings(self):
        """swap.js reads the island, the template renders the list.

        They are produced from the same data and must not diverge -- a panel
        showing one set of assets while the controller swaps against another
        is the worst kind of disagreement.
        """
        self.client.force_login(_make_linked_user())

        response = self.client.get(self.url)
        island = json.loads(str(response.context["holdings_json"]))

        self.assertEqual(
            island,
            response.context["holdings"],
            "the JSON island and the rendered holdings disagree",
        )

    def test_integration_an_unlinked_user_is_refused(self):
        """Linkage is the gate: holdings are readable only for your own address."""
        stranger = get_user_model().objects.create_user(
            username="stranger@example.com",
            email="stranger@example.com",
            password="top_secret",
        )
        stranger.profile.permission = 100
        stranger.profile.save()
        self.client.force_login(stranger)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            403,
            "a user with no linkage to this address was served its holdings",
        )

    def test_integration_an_anonymous_visitor_is_sent_to_log_in(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)


class SwapAssetsViewTest(TestCase):
    """Testing class for the target-asset search partial."""

    def setUp(self):
        self.url = reverse("swap_assets")

    def test_integration_asset_search_renders_matches(self):
        self.client.force_login(_make_linked_user())

        response = self.client.get(self.url, {"q": KNOWN_QUERY})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "swap/_assets.html")
        self.assertEqual(response.context["query"], KNOWN_QUERY)
        self.assertTrue(
            response.context["assets"],
            f"no assets rendered for {KNOWN_QUERY!r}",
        )

    def test_integration_an_empty_query_skips_the_engine(self):
        """Typing and clearing the box must not cost a backend round trip."""
        self.client.force_login(_make_linked_user())

        response = self.client.get(self.url, {"q": "   "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query"], "")
        self.assertEqual(response.context["assets"], [])

    def test_integration_an_anonymous_visitor_is_sent_to_log_in(self):
        """Asset metadata is public, but the endpoint is not anonymous."""
        response = self.client.get(self.url, {"q": KNOWN_QUERY})

        self.assertEqual(response.status_code, 302)
