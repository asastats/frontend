"""Integration tests for the dynamic address designs against the backend.

``test_address_page_integration.py`` covers the same page for design 1. It
cannot cover these, and not by oversight: it uses an anonymous client, and an
anonymous reader always resolves to ``address.html``. The dynamic designs
are reached only by a signed-in reader at Asastatser with the layout chosen, so
the most backend-dependent page in the project had a whole second and third
rendering of the live payload that nothing had ever run.

What that hid, and what these tests exist for:

**Positions reached the page without an identity.** ``pid`` is the *website's*
name for a position -- the engine does not emit one. It was added by
``AsaItemSerializer.to_representation``, which runs when the website *serves*
``/api/v2/``; the address page consumes the engine's payload through
``fetch_and_serialize_account`` and never touches that serializer. So against
the real backend the page rendered 27 positions and **zero** ``data-pid``
attributes, which means zero pin controls: ``pins.js``, its 100%-covered jest
suite, the pinned band and the whole position-pinning feature were dead in
production. Every test passed throughout, because each fixture called
``annotate_positions`` on itself before rendering -- the tests fabricated the
one condition the page never had. The annotation moved to
:func:`api.main.fetch_and_serialize_account`, which is the layer where the page
and the API meet.

That is the shape of thing only an integration test finds, so the rules here
are the same ones ``test_address_page_integration.py`` set:

* assert against ``response.context`` where the question is about data;
* anchor on ``id="f<asset id>"``, ``data-val``, ``data-pid`` where the question
  is about the rendered page -- attributes the scripts select on;
* never assert a presentation class, which the design is entitled to change.
"""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from api.main import fetch_and_serialize_account
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

#: The same light mainnet address design 1's integration tests use: 11 assets,
#: 2 NFT collections, 27 positions across 8 assets that hold more than one --
#: enough to exercise venue grouping, and small enough to stay inside the
#: backend read timeout.
LIGHT_ADDRESS = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M"

ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]


def _reader(username, permission=ASASTATSER, layout="dynamic"):
    """Create a signed-in client for a reader on ``layout``.

    ``force_login`` rather than ``login``: the ``user_logged_in`` receiver in
    ``core/signals.py`` calls ``check_votes_and_permission`` for an authorized
    profile, which would go to the permission dApp and overwrite the tier under
    test. The profile here is left unauthorized, so nothing refreshes.

    :return: tuple of (:class:`Client`, :class:`User`)
    """
    user = get_user_model().objects.create(
        username=username, email=f"{username}@example.com"
    )
    user.profile.permission = permission
    user.profile.preferred_layout = layout
    user.profile.save()

    client = Client()
    client.force_login(user)
    return client, user


class DynamicDataTest(TestCase):
    """What the backend returned, as the dynamic view received it."""

    @classmethod
    def setUpClass(cls):
        # One live evaluation shared by the class; asserting different facets
        # of the same response is the point. Not setUpTestData, which
        # deep-copies what it stores and cannot pickle a response's
        # ResolverMatch.
        super().setUpClass()
        cache.clear()
        client, _ = _reader("money-data")
        cls.response = client.get(f"/{LIGHT_ADDRESS}")

    def test_integration_a_subscriber_gets_the_money_column(self):
        """Guard the guard: everything below reads this response."""
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, "address_dynamic.html")
        self.assertEqual("dynamic", self.response.context["layout"])
        self.assertFalse(self.response.context["compact"])

    def test_integration_the_money_column_carries_a_populated_payload(self):
        """An empty evaluation would satisfy every 200-and-template test."""
        account = self.response.context["account"]

        self.assertEqual(account["account_info"]["addresses"], [LIGHT_ADDRESS])
        self.assertTrue(account["asaitems"], "no asset rows came back")
        self.assertTrue(account["nftcollections"], "no NFT collections came back")
        self.assertTrue(float(account["total"]["total"]) > 0, "total evaluates to zero")

    def test_integration_every_position_has_an_identity(self):
        """The regression this module was written for.

        The engine does not emit ``pid``; the website computes it. If that
        annotation is not applied on the page's own path, every position
        arrives anonymous and the page silently renders no pin control at all
        -- which is what it did.
        """
        account = self.response.context["account"]
        positions = [
            (item["asset"]["id"], program)
            for item in account["asaitems"]
            for program in (item.get("programs") or [])
        ]
        self.assertTrue(positions, "the payload carried no positions to identify")

        anonymous = [
            asset_id for asset_id, program in positions if not program.get("pid")
        ]
        self.assertEqual(
            anonymous,
            [],
            f"{len(anonymous)} of {len(positions)} positions reached the page "
            "without a pid, so the page renders no pin control for them. The "
            "annotation belongs in api.main.fetch_and_serialize_account -- the "
            "serializer that also does it only runs when we *serve* /api/v2/.",
        )

    def test_integration_ambiguity_is_always_reported(self):
        """Never omitted when false.

        A flag that is absent when false forces every consumer to tell "not
        ambiguous" apart from "this build does not report it", and `pins.js`
        treats presence as the signal.
        """
        account = self.response.context["account"]
        programs = [
            program
            for item in account["asaitems"]
            for program in (item.get("programs") or [])
        ]

        missing = [p["pid"] for p in programs if "pid_ambiguous" not in p]
        self.assertEqual(missing, [], f"pid_ambiguous omitted for {missing}")

    def test_integration_identities_are_stable_across_evaluations(self):
        """A pin is worth nothing if the id moves between two page loads.

        Two live evaluations of the same address. Values legitimately differ
        between them -- the price moves -- and the ids must not, which is the
        entire reason the id is built from what a position *is* rather than
        from its value or its rank.
        """
        first = fetch_and_serialize_account(LIGHT_ADDRESS, LIGHT_ADDRESS)
        second = fetch_and_serialize_account(LIGHT_ADDRESS, LIGHT_ADDRESS)

        def ids(payload):
            return [
                (item["asset"]["id"], program.get("pid"))
                for item in payload["asaitems"]
                for program in (item.get("programs") or [])
            ]

        self.assertEqual(ids(first), ids(second), "position ids moved between loads")

    def test_integration_identities_are_versioned(self):
        """`PID_VERSION` rides along, so stale saved pins are recognisable."""
        account = self.response.context["account"]
        pids = [
            program["pid"]
            for item in account["asaitems"]
            for program in (item.get("programs") or [])
        ]

        self.assertTrue(pids)
        self.assertTrue(
            all(pid.startswith("p1-") for pid in pids),
            f"unversioned position ids: {[p for p in pids if not p.startswith('p1-')][:5]}",
        )


class DynamicRenderTest(TestCase):
    """Payload values reaching the rendered dynamic page.

    The half a template can break: the data can be perfectly correct in the
    context and never make it onto the page.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        client, _ = _reader("money-render")
        cls.response = client.get(f"/{LIGHT_ADDRESS}")
        cls.html = cls.response.content.decode()
        cls.account = cls.response.context["account"]

    def test_integration_every_asset_row_is_rendered(self):
        """One `id="f<asset id>"` anchor per asaitem, none missing.

        The same anchors design 1 uses, kept deliberately: `pins.js` finds an
        entry with `closest('.fitem')` and a reader's saved arrangement is
        remembered against these ids, so reusing them is what lets an
        arrangement survive switching designs.
        """
        missing = [
            item["asset"]["id"]
            for item in self.account["asaitems"]
            if f'id="f{item["asset"]["id"]}"' not in self.html
        ]

        self.assertEqual(
            missing,
            [],
            f"{len(missing)} of {len(self.account['asaitems'])} asset rows are "
            f"in the context but not on the page: {missing}",
        )

    def test_integration_every_asset_value_is_rendered(self):
        """`data-val` carries the payload's value, unrounded.

        The visible text is rounded; `data-val` is what the ALGO/USD switch
        recomputes from, so it is the one that has to match exactly.
        """
        missing = [
            (item["asset"]["unit"], item["value"])
            for item in self.account["asaitems"]
            if f'data-val="{item["value"]}"' not in self.html
        ]

        self.assertEqual(missing, [], f"values that never reached the page: {missing}")

    def test_integration_every_position_identity_is_rendered(self):
        """In the context is not on the page.

        `data-pid` is what a pin is stored against, so a position whose id
        stops being written is a position that cannot be pinned -- and nothing
        visible changes.
        """
        pids = [
            program["pid"]
            for item in self.account["asaitems"]
            for program in (item.get("programs") or [])
        ]
        missing = [pid for pid in pids if f'data-pid="{pid}"' not in self.html]

        self.assertEqual(
            missing, [], f"{len(missing)} of {len(pids)} position ids never rendered"
        )

    def test_integration_every_position_offers_a_pin(self):
        """The control is rendered at rest for everybody.

        It cannot be rendered pressed: this page's cache entry is shared
        between readers on the same layout, so the markup ships every control
        unpressed and the reader's own browser sets the ones belonging to them.
        What the server owes is that the control exists at all -- one per
        position, which is what was missing entirely.
        """
        pids = [
            program["pid"]
            for item in self.account["asaitems"]
            for program in (item.get("programs") or [])
        ]

        self.assertEqual(
            len(pids),
            self.html.count("data-pin-position="),
            "the number of pin controls does not match the number of positions",
        )

    def test_integration_venue_subtotals_add_up_to_the_asset(self):
        """Grouping must not invent an answer.

        Computed from the live payload rather than a fixture, because
        ``program_groups`` groups on ``program.name`` and what the engine puts
        there varies by position type -- a venue for most, the category
        "Liquidity" for LP positions. A fixture agrees with itself by
        construction.
        """
        checked = 0
        for item in self.account["asaitems"]:
            programs = item.get("programs") or []
            if not programs:
                continue
            groups = {}
            for program in programs:
                name = ((program.get("program") or {}).get("name")) or ""
                groups[name] = groups.get(name, 0) + float(program.get("value") or 0)

            with self.subTest(asset=item["asset"]["unit"]):
                self.assertAlmostEqual(
                    float(item["value"]),
                    sum(groups.values()),
                    delta=0.01,
                    msg=f"{item['asset']['unit']}: header {item['value']} vs "
                    f"venues {sum(groups.values())}",
                )
            checked += 1

        self.assertGreater(checked, 0, "no asset carried positions to check")

    def test_integration_the_allocation_band_reports_the_nft_holding(self):
        """The bug that shipped, against live numbers.

        ``consolidated`` is a namedtuple and ``account.total`` is a plain dict,
        so reading both with ``getattr`` returned 0 for every NFT holding --
        the band drew four categories summing to 100% while omitting what was,
        on the reference address, the largest one. Nothing raised.
        """
        held = float(self.account["total"]["nft"])
        if not held:
            self.skipTest("this address holds no valued NFTs")

        consolidated = self.response.context["consolidated"]
        values = {
            "balance": float(consolidated.balance),
            "staked": float(consolidated.staked),
            "liquidity": float(consolidated.liquidity),
            "defi": float(consolidated.defi),
            "nft": held,
        }
        summed = sum(abs(value) for value in values.values())
        share = abs(values["nft"]) / summed * 100

        # On the page, not merely in the context: the band renders the share to
        # one decimal place, and 0.0 is what the bug looked like.
        self.assertGreater(share, 0, "the NFT band computed to zero")
        self.assertIn(
            f'data-val="{values["nft"]}"',
            self.html,
            "the NFT figure never reached the allocation band",
        )

    def test_integration_the_charts_ship_their_payloads(self):
        """`dynamic.js` draws from the json_script blocks, not from the markup.

        Design 1's canvases are absent here, so an empty payload block is not
        visible as a missing chart -- the panel simply says there is nothing to
        chart.
        """
        for block in ("asachart", "nftchart", "ratiochart", "distchart"):
            with self.subTest(block=block):
                self.assertIn(f'id="{block}"', self.html)

        self.assertNotIn("chart.min.js", self.html, "the money column shipped Chart.js")


class DynamicEntitlementTest(TestCase):
    """Who gets which page, and what the shared cache entry may carry.

    ``cache_page`` is a *view* decorator, so ``Vary: Cookie`` is appended by
    ``SessionMiddleware`` after ``learn_cache_key`` has already recorded what
    to key on -- two readers share one entry. The layout escapes that only
    because ``dispatch`` folds it into the key prefix. Asserted here against
    live renders, where a leak would hand a free reader a paid design.
    """

    def setUp(self):
        super().setUp()
        cache.clear()

    def test_integration_a_reader_below_the_tier_gets_design_one(self):
        """The saved choice is kept, and it does not apply."""
        client, user = _reader("money-lapsed", permission=0, layout="dynamic")

        response = client.get(f"/{LIGHT_ADDRESS}")

        self.assertTemplateUsed(response, "address.html")
        user.profile.refresh_from_db()
        self.assertEqual("dynamic", user.profile.preferred_layout)

    def test_integration_two_readers_on_two_layouts_get_two_pages(self):
        """The case that discriminates.

        Anonymous-then-authenticated proves nothing: the first request
        populates the entry and the second is a different reader only by luck
        of ordering. Two *signed-in* readers on different layouts is the pair
        that fails if the layout is not in the key.
        """
        paid, _ = _reader("money-paid", layout="dynamic")
        free, _ = _reader("money-free", permission=0, layout="")

        paid_response = paid.get(f"/{LIGHT_ADDRESS}")
        free_response = free.get(f"/{LIGHT_ADDRESS}")

        self.assertTemplateUsed(paid_response, "address_dynamic.html")
        self.assertTemplateUsed(free_response, "address.html")
        self.assertNotIn(b"dynamic-page", free_response.content)

    def test_integration_the_free_reader_first_does_not_poison_the_paid_one(self):
        """The same pair in the other order, because a cache is order-sensitive."""
        free, _ = _reader("money-free-2", permission=0, layout="")
        paid, _ = _reader("money-paid-2", layout="dynamic")

        free_response = free.get(f"/{LIGHT_ADDRESS}")
        paid_response = paid.get(f"/{LIGHT_ADDRESS}")

        self.assertTemplateUsed(free_response, "address.html")
        self.assertTemplateUsed(paid_response, "address_dynamic.html")

    def test_integration_the_compact_layout_is_the_same_page_denser(self):
        """One template, two layouts, and the compact flag is the difference."""
        client, _ = _reader("money-compact", layout="dynamic-compact")

        response = client.get(f"/{LIGHT_ADDRESS}")

        self.assertTemplateUsed(response, "address_dynamic.html")
        self.assertTrue(response.context["compact"])
        self.assertIn(b'class="rows cards"', response.content)

    def test_integration_the_compact_entry_has_its_own_cache_entry(self):
        """Two layouts sharing a template must not share a cache entry.

        `layout_template` is deliberately not an identity -- the money column
        and its compact form name the same file -- so a key built from the
        template rather than the layout would serve one of them the other's
        bytes.
        """
        wide, _ = _reader("money-wide-3", layout="dynamic")
        compact, _ = _reader("money-compact-3", layout="dynamic-compact")

        wide_response = wide.get(f"/{LIGHT_ADDRESS}")
        compact_response = compact.get(f"/{LIGHT_ADDRESS}")

        self.assertNotIn(b'class="rows cards"', wide_response.content)
        self.assertIn(b'class="rows cards"', compact_response.content)
