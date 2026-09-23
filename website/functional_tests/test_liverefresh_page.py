"""The address page updating itself from the engine's published block.

Everything under this feature is covered by unit tests - the engine's diff, the
widget's fragments, the timer in `address.js` - and none of it answers the
question the feature exists for: does the page change under a reader without
taking anything away from them?

That is a browser question and only a browser can answer it, and the answer has
two sides that unit tests cannot hold together.

**A price move must not reload.** That is most blocks for most pages, it is what
the free tier does instead, and the whole point of the subscriber path is that it
does not. What the reader had open must survive it - a poll that swapped the
right figures while closing an open row would pass every test in this repo except
these.

**A holdings change must reload**, and this is the half that was missing. An
out-of-band swap can only reach a row the page already has, so an asset just
bought has nowhere to arrive and one just sold is never mentioned; the only thing
that renders rows is the page itself. The two cases are told apart by the
holdings fingerprint the page was rendered from, which it sends back with every
poll - so both halves are the same mechanism seen from two sides, and testing
only the first one (as this file did) leaves the reader's page silently wrong
about what they hold.
"""

import json
import os
import time
from unittest import mock

import msgpack
from django.contrib.auth import get_user_model
from django.core.cache import cache
from selenium.webdriver.common.by import By
from utils.constants.core import LIVEREFRESH_POLL_SECONDS
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

from .base import COOKIE_SEED_URL, FunctionalTest

SAMPLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "utils",
    "tests",
    "sample_serialized_540A5.json",
)

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
INTRO = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]

#: Deliberately unlike anything in the sample, so an assertion that finds it
#: cannot be reading the server-rendered page by accident.
PUBLISHED_TOTAL = 4242.424242

#: What the page is rendered from. `<counter>:<digest of the asset ids>`, as
#: `utils.transmitters._holdings_fingerprint` builds it.
RENDERED_FINGERPRINT = "7:abc123def456"
#: The same page under the split fingerprint: `<counter>:<assets>:<positions>`.
#: Two-part fingerprints stay in the tests above deliberately - they are what a
#: page rendered by an older engine carries, and those must still reload.
RENDERED_FINGERPRINT_SPLIT = "7:abc123def456:pos000000"
#: After a position opened: the asset half stands, the position half moved. The
#: counter steps too, because the block that opened it named the account.
REGROUPED_FINGERPRINT = "8:abc123def456:pos111111"
#: The same holdings after a block named the account: the counter has stepped
#: and the digest has not, so the asset set is unchanged and only figures moved.
#:
#: **This used to be what `MOVED_FINGERPRINT` meant, and it used to reload.**
#: That was right while an amount could not be sent as a fragment - a counter
#: step is exactly how an amount moves, and the rebuild was the only thing that
#: corrected it. Now that `_live_payload` publishes amounts, this case is
#: carried out of band and the reader keeps their scroll, their filters and
#: every collection they had opened.
STRUCK_FINGERPRINT = "8:abc123def456"
#: The account bought or sold something: the **digest** has moved, so the asset
#: set itself is different. A fragment cannot create a row for an asset that has
#: just arrived, which is the one case that still has to rebuild the page.
MOVED_FINGERPRINT = "8:0ff113579bdf"


def _sample_payload():
    with open(SAMPLE_PATH) as sample_file:
        return json.load(sample_file)


class LiveRefreshTest(FunctionalTest):
    """A subscriber watching the page keep up with the chain."""

    def setUp(self):
        super().setUp()
        cache.clear()
        self.sample = _sample_payload()
        self.first = self.sample["asaitems"][0]
        # **Pinned, because the real one reads the engine's Redis.** The address
        # page renders `data-holdings` from `cached_live_holdings`, and on a
        # machine where the engine is running and something is watching this
        # address that answers with a real fingerprint - which will not match
        # whatever a test publishes, so every poll orders a reload and every
        # assertion about updating in place fails. These tests passed for an
        # afternoon only because nothing happened to be watching it.
        self.fingerprints = [RENDERED_FINGERPRINT]
        patcher = mock.patch(
            "core.views.cached_live_holdings",
            side_effect=lambda *a, **kw: (
                self.fingerprints.pop(0)
                if len(self.fingerprints) > 1
                else self.fingerprints[0]
            ),
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def sign_in(self, live_refresh=True, permission=ASASTATSER):
        """Log a reader in on the dynamic layout, opted in or not."""
        cookie = self.create_session_cookie(
            username="live@example.com", password="top_secret", permission=permission
        )
        profile = get_user_model().objects.get(username="live@example.com").profile
        profile.preferred_layout = "dynamic"
        profile.live_refresh = live_refresh
        profile.save()
        self.browser.get(self.server_url + COOKIE_SEED_URL)
        self.browser.add_cookie(cookie)

    #: Design 1 renders no positions at all, so its subclass skips the two
    #: position tests rather than asserting against markup that cannot exist.
    RENDERS_POSITIONS = True

    def _published(
        self, values=None, holdings=RENDERED_FINGERPRINT, positions=None
    ):
        """Return a msgpack block as the engine's pass publishes one."""
        total = self.sample["total"]
        return msgpack.packb(
            {
                "holdings": holdings,
                "total": PUBLISHED_TOTAL,
                "algo": total["algo"],
                "asa": total["asa"],
                "nft": total["nft"],
                "totalusdc": total["totalusdc"],
                "priceusdc": total["priceusdc"],
                "pricealgo": total["pricealgo"],
                "values": values or {},
                "positions": positions or [],
                "round": 64595872,
            }
        )

    def _redis(
        self,
        values=None,
        holdings=RENDERED_FINGERPRINT,
        positions=None,
        snapshot=None,
    ):
        """A client that answers with one published block and records the beat.

        **Keyed by prefix once a snapshot is involved.** The widget reads two
        things out of this Redis now - `lvp:` for the block's diff and `lvn:`
        for the account a venue group is re-rendered from - and a client that
        answers every `get` with the diff would hand the regroup a payload
        where it expects an account, which reads as "no snapshot" and falls
        back to the reload this is trying to prove it does not need.
        """
        client = mock.MagicMock()
        block = self._published(values, holdings, positions)
        if snapshot is None:
            client.get.return_value = block
            return client

        packed = msgpack.packb({"holdings": holdings, "account": snapshot})

        def answer(key, *args, **kwargs):
            return packed if str(key).startswith("lvn:") else block

        client.get.side_effect = answer
        return client

    def _opened_position(self, sample, asset_id):
        """Return `sample` with one more position under `asset_id`.

        Named after the report: a Mallow directional position, which is what
        the reader opened while watching the page. The name is what the test
        looks for, because it is the one thing on the row that cannot have come
        from the server-rendered page.
        """
        from copy import deepcopy

        from api.position_id import annotate_positions

        opened = deepcopy(sample)
        for item in opened["asaitems"]:
            if item["asset"]["id"] != asset_id:
                continue
            item["programs"].append(
                {
                    "program": {
                        "type": "Staked",
                        "name": "Mallow (ALGO down)",
                        "provider": {"name": "Mallow"},
                        "url": "https://usemallow.app/",
                        "code": "",
                    },
                    "value": 22.0,
                    "amount": 5500000,
                    "linked": [],
                    "distribution": [],
                }
            )
        for item in opened["asaitems"]:
            annotate_positions(item["asset"]["id"], item["programs"])
        return opened

    def _annotated_sample(self):
        """Return the sample with every position given its `pid`.

        **`fetch_and_serialize_account` is what annotates, and this suite mocks
        it.** So a page built from the raw sample renders positions with no
        identity - no `data-pid`, no element ids - and a fragment addressed at
        one lands nowhere. That is the same gap `api/main.py` records from the
        other direction: the whole position-pinning feature was dead against
        the real backend while passing every test, because the fixtures
        annotated themselves.
        """
        from copy import deepcopy

        from api.position_id import annotate_positions

        sample = deepcopy(self.sample)
        for item in sample["asaitems"]:
            annotate_positions(item["asset"]["id"], item["programs"])
        return sample

    def _a_position(self, sample):
        """Return (asset id, program) for a position `sample` names.

        Skips the ambiguous ones deliberately: the page gives those no element
        id, so a fragment for one has nowhere to land and would prove nothing.
        """
        for item in sample["asaitems"]:
            for program in item["programs"]:
                if program.get("pid") and not program.get("pid_ambiguous"):
                    return item["asset"]["id"], program
        raise AssertionError("the sample bundle names no position")

    @staticmethod
    def _as_published(asset_id, program, value):
        """Return `program` as the engine publishes it, at a new value."""
        detail = program.get("program") or {}
        provider = detail.get("provider") or {}
        return {
            "asset": asset_id,
            "fields": {
                "type": detail.get("type") or "",
                "name": detail.get("name") or "",
                "provider": provider.get("name") or "",
                "code": detail.get("code") or "",
                "url": detail.get("url") or "",
            },
            "links": [
                [link.get("text") or "", str(link["id"])]
                for link in (program.get("linked") or [])
                if link.get("id") is not None
            ],
            "value": value,
            "amount": program.get("amount") or 0,
            "decimals": 6,
            "breakdown": bool(program.get("distribution")),
        }

    def _rendered_fingerprint(self, *fingerprints):
        """Set what the address page renders `data-holdings` from.

        One value means every render carries it. Two means the first render
        carries the first and everything after carries the second, which is what
        a real reload sees: the page is keyed on this, so once the engine has
        published a new one the rebuilt page carries it and the reader settles
        rather than looping.
        """
        self.fingerprints[:] = list(fingerprints)

    def holdings_attribute(self):
        """Return what the page says it was rendered from."""
        return self.browser.execute_script(
            "var el = document.querySelector('[data-holdings]');"
            "return el && el.dataset.holdings;"
        )

    def open_page(self):
        """Load the address page and wait for the per-reader partial."""
        self.record_javascript_errors()
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.wait_until(
            lambda: self.browser.execute_script(
                "return !!(window.asastatsToolbar && window.asastatsToolbar.state());"
            )
        )

    def arm(self):
        """Tick the Auto-refresh checkbox, which is what starts the poll."""
        self.browser.execute_script("localStorage.setItem('refresh', 'y');")

    #: Where the band's data attributes live. The dynamic layout puts them on
    #: the swapped element itself; classic puts them on the `.pricetip` inside
    #: the swapped `.tooltip` wrapper.
    BAND_DATA = "#id-band-total"

    def value_text(self, figure):
        """Return what a row's value span reads after an update.

        Classic renders the unit inside the span and the dynamic layout keeps it
        in a sibling, so the same published figure is different text.
        """
        return figure

    def band(self):
        """Return the total the band is showing."""
        return self.browser.execute_script(
            "var el = document.getElementById('id-band-total');"
            "return el && el.textContent.trim();"
        )

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_band_takes_the_published_block_without_reloading(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """**The reload is the thing being avoided, so it is what is asserted.**

        A sentinel is written onto `window` before the poll and read after it.
        A page that reloaded would lose it, and would also pass an assertion
        that only checked the figure - because the server renders that figure
        too. The two together are what separate "updated in place" from
        "fetched again".
        """
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = self._redis()

        self.sign_in()
        self.open_page()
        before = self.band()
        self.arm()
        self.browser.execute_script("window.__stillHere = true;")

        self.wait_until(lambda: self.band() != before, timeout=15)

        assert "4,242.42" in self.band()
        assert self.browser.execute_script("return window.__stillHere;") is True

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_page_carries_the_fingerprint_it_was_rendered_from(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """Without this on the page there is nothing to compare a published
        block against, and the reload can never be asked for."""
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = self._redis()
        self._rendered_fingerprint(RENDERED_FINGERPRINT)

        self.sign_in()
        self.open_page()

        assert self.holdings_attribute() == RENDERED_FINGERPRINT

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_holdings_change_reloads_the_page(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """**The half no fragment can do, asserted the only way it shows.**

        The account transacted, so the engine's fingerprint has moved past the
        one this page was built with. An out-of-band swap cannot add the row
        they bought or remove the one they sold, so the widget answers
        `HX-Refresh` and the page rebuilds itself.

        The sentinel is the assertion, and it is the exact inverse of the one
        next door: a page that merely swapped figures would keep it. Checking
        the figures instead would prove nothing, because the server renders
        those too.
        """
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        # Published ahead of what the page was rendered from.
        mocked_redis.return_value = self._redis(holdings=MOVED_FINGERPRINT)
        self._rendered_fingerprint(RENDERED_FINGERPRINT, MOVED_FINGERPRINT)

        self.sign_in()
        self.open_page()
        self.arm()
        self.browser.execute_script("window.__stillHere = true;")

        self.wait_until(
            lambda: self.browser.execute_script("return !window.__stillHere;"),
            timeout=15,
        )

        assert self.holdings_attribute() == MOVED_FINGERPRINT

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_position_figure_lands_on_the_row_it_belongs_to(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """**The join, proved in a browser rather than against a fixture.**

        The engine cannot name a position and the page cannot value one: the
        live pass never serializes, so it sends what the position *is* and the
        view turns that into the `pid` the row was given. Everything under this
        has a unit test, and every one of them builds its own DOM - which is
        exactly how a swap that lands nowhere stays green.

        Nothing but a real page can say the id the engine's fields hash to is
        the id the template wrote.
        """
        if not self.RENDERS_POSITIONS:
            self.skipTest("design 1 renders no positions")
        sample = self._annotated_sample()
        asset_id, program = self._a_position(sample)
        mocked_fetch.return_value = sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = self._redis(
            positions=[self._as_published(asset_id, program, 1234.5)]
        )
        self._rendered_fingerprint(RENDERED_FINGERPRINT)

        self.sign_in()
        self.open_page()
        self.arm()

        target = f"pv-{program['pid']}"
        self.wait_until(
            lambda: self.browser.execute_script(
                "var el = document.getElementById(arguments[0]);"
                "return el && el.getAttribute('data-val') === '1234.5';",
                target,
            ),
            timeout=15,
        )

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_position_figure_carries_its_total_with_it(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """**The property a whole-position swap would have given for free.**

        `data-value` is on the `.position` itself and is what `toolbar.js` sums
        for every category total and the allocation band. A fragment cannot
        reach an attribute without replacing the element that holds it, so the
        page would go on totalling the figure the position no longer has - the
        headline drifting away from its own rows, which is the failure that
        made narrowing the reload a mistake the first time.

        Swapping the whole `.position` was the alternative and costs 17x the
        bytes; this is what has to be true for the cheap version to be right.
        """
        if not self.RENDERS_POSITIONS:
            self.skipTest("design 1 renders no positions")
        sample = self._annotated_sample()
        asset_id, program = self._a_position(sample)
        mocked_fetch.return_value = sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = self._redis(
            positions=[self._as_published(asset_id, program, 1234.5)]
        )
        self._rendered_fingerprint(RENDERED_FINGERPRINT)

        self.sign_in()
        self.open_page()
        self.arm()

        target = f"pv-{program['pid']}"
        self.wait_until(
            lambda: self.browser.execute_script(
                "var el = document.getElementById(arguments[0]);"
                "return el && el.getAttribute('data-val') === '1234.5';",
                target,
            ),
            timeout=15,
        )

        assert self.browser.execute_script(
            "var el = document.getElementById(arguments[0]);"
            "var row = el && el.closest('.position');"
            "return row && row.getAttribute('data-value');",
            target,
        ) == "1234.5"

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_struck_account_keeps_its_page_and_its_positions_move(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """**Both halves of the bargain, in one test, deliberately.**

        A block named the account so the counter stepped; the asset set did not
        change. The page must not rebuild - that is the reload this work exists
        to retire - *and* a position's figure must arrive anyway, because the
        rebuild was the only thing that used to correct one.

        Asserting only the first half is what made narrowing this a mistake on
        2026-09-19: the page stopped reloading, every position froze, and the
        row total above them stayed live. One assertion cannot catch that; the
        pair can.
        """
        if not self.RENDERS_POSITIONS:
            self.skipTest("design 1 renders no positions")
        sample = self._annotated_sample()
        asset_id, program = self._a_position(sample)
        mocked_fetch.return_value = sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = self._redis(
            holdings=STRUCK_FINGERPRINT,
            positions=[self._as_published(asset_id, program, 1234.5)],
        )
        self._rendered_fingerprint(RENDERED_FINGERPRINT)

        self.sign_in()
        self.open_page()
        self.arm()
        self.browser.execute_script("window.__stillHere = true;")

        target = f"pv-{program['pid']}"
        self.wait_until(
            lambda: self.browser.execute_script(
                "var el = document.getElementById(arguments[0]);"
                "return el && el.getAttribute('data-val') === '1234.5';",
                target,
            ),
            timeout=15,
        )

        # The sentinel is how "did not reload" shows: a rebuilt page loses it.
        assert self.browser.execute_script("return window.__stillHere;") is True
        assert self.holdings_attribute() == RENDERED_FINGERPRINT

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_new_position_arrives_without_reloading_the_page(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """**The reported case, and the thing this whole path is for.**

        A Mallow position opened on an account that already held the asset. No
        asset arrived, so nothing on this page needs rebuilding - but until the
        two digests were published apart it was indistinguishable from buying
        one, and the reader lost their scroll, their filters and every open
        section to a full reload to gain one row. Reported 2026-09-23, watched
        live while staking.

        The sentinel is the assertion and it is the exact inverse of
        `test_a_holdings_change_reloads_the_page`: a rebuilt page loses it, so
        finding it *and* the new row is the whole claim. Asserting the row
        alone would pass on a reload, which is what used to happen.
        """
        if not self.RENDERS_POSITIONS:
            self.skipTest("design 1 renders no positions")
        sample = self._annotated_sample()
        asset_id, program = self._a_position(sample)
        mocked_fetch.return_value = sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}

        # The snapshot the engine publishes on the block that changed the
        # positions: the same account, plus one position the page has never
        # seen. A copy rather than the sample itself - the page is rendered
        # from that, and a row already on it would prove nothing.
        opened = self._opened_position(sample, asset_id)
        mocked_redis.return_value = self._redis(
            holdings=REGROUPED_FINGERPRINT, snapshot=opened
        )
        self._rendered_fingerprint(RENDERED_FINGERPRINT_SPLIT)

        self.sign_in()
        self.open_page()
        self.arm()
        self.browser.execute_script("window.__stillHere = true;")

        self.wait_until(
            lambda: self.browser.execute_script(
                "return !!document.querySelector("
                "'.position[data-search*=\"Mallow (ALGO down)\"]');"
            ),
            timeout=20,
        )

        # Still the same document: the row arrived in place.
        assert self.browser.execute_script("return window.__stillHere;") is True
        # And the page has caught up, so it stops asking for the same regroup.
        assert self.holdings_attribute() == REGROUPED_FINGERPRINT

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_reader_is_not_reloaded_round_and_round(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """**A reload that does not settle is worse than no reload at all.**

        The rebuilt page is keyed on the same fingerprint the engine published,
        so it comes back carrying it and the next poll agrees. Were the address
        page's cache entry not keyed on it, the reader would be handed the very
        markup that prompted the reload and sent round again, for ever.
        """
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = self._redis(holdings=MOVED_FINGERPRINT)
        self._rendered_fingerprint(RENDERED_FINGERPRINT, MOVED_FINGERPRINT)

        self.sign_in()
        self.open_page()
        self.arm()
        self.browser.execute_script("window.__stillHere = true;")
        self.wait_until(
            lambda: self.browser.execute_script("return !window.__stillHere;"),
            timeout=15,
        )

        # Settled: a fresh sentinel has to survive more than two poll intervals,
        # so a second reload anywhere in that window fails this.
        self.browser.execute_script("window.__settled = true;")
        time.sleep(LIVEREFRESH_POLL_SECONDS * 3)

        assert self.browser.execute_script("return window.__settled;") is True
        assert self.holdings_attribute() == MOVED_FINGERPRINT

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_price_move_leaves_the_page_where_it_is(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """The other side of the same mechanism, and the common one.

        The fingerprint has not moved, because no holding has: only what they
        are worth. Reloading here would throw the reader's page away every few
        seconds for figures the fragments swap perfectly well.
        """
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = self._redis(holdings=RENDERED_FINGERPRINT)
        self._rendered_fingerprint(RENDERED_FINGERPRINT)

        self.sign_in()
        self.open_page()
        before = self.band()
        self.arm()
        self.browser.execute_script("window.__stillHere = true;")

        self.wait_until(lambda: self.band() != before, timeout=15)

        assert "4,242.42" in self.band()
        assert self.browser.execute_script("return window.__stillHere;") is True

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_an_open_row_survives_the_update(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """What the free tier's reload cannot do, and the reason for all of it.

        The row is opened first, then the block arrives changing that row's own
        figure. Swapping the `<details>` rather than the figure inside it would
        close it - and the reader would lose their place every few seconds,
        which is worse than a page that never updated.
        """
        asset_id = self.first["asset"]["id"]
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = self._redis({asset_id: 99.5})

        self.sign_in()
        self.open_page()
        self.browser.execute_script(
            "document.getElementById('f' + arguments[0]).open = true;", asset_id
        )
        self.arm()

        self.wait_until(
            lambda: self.browser.execute_script(
                "var el = document.getElementById('v' + arguments[0]);"
                "return el && el.textContent.trim() === arguments[1];",
                asset_id,
                self.value_text("99.50"),
            ),
            timeout=15,
        )

        assert self.browser.execute_script(
            "return document.getElementById('f' + arguments[0]).open;", asset_id
        ) is True

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_currency_switch_still_works_on_a_swapped_band(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """The band is replaced whole, and `address.js` reads its attributes.

        An update that dropped one of them would leave the switch computing
        from `undefined` and rendering NaN - a block after the reader last
        touched anything, which is exactly when nobody is looking.
        """
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = self._redis()

        self.sign_in()
        self.open_page()
        before = self.band()
        self.arm()
        self.wait_until(lambda: self.band() != before, timeout=15)

        dataset = self.browser.execute_script(
            "var el = document.querySelector(arguments[0]);"
            "return {price: el.dataset.price, pricealgo: el.dataset.pricealgo,"
            "        total: el.dataset.total, totalwnft: el.dataset.totalwnft,"
            "        totalnft: el.dataset.totalnft};",
            self.BAND_DATA,
        )

        for name, value in dataset.items():
            assert value not in (None, "", "None"), name

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_page_over_the_readers_warm_set_stays_put(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """**A second page beyond the tier's addresses goes static, quietly.**

        Asastatser buys one address. Their second tab passes its own size-1
        access check, so before the warm set the engine re-priced both; now the
        second one is not warmed at all.

        What a reader must see is *nothing*: the figures simply do not move.
        No error, no banner, no reload - the same thing a page shed by
        admission control already does, on a tab they are probably not looking
        at. So this asserts the band is unchanged **and** that the page is
        still the one that was loaded, because a reload would also leave the
        band reading what the server rendered and would pass a figure-only
        check.
        """
        import time as _time

        client = self._redis()
        # This reader's one slot is held by another page that is **still
        # polling**, so it cannot be taken.
        #
        # The score has to be computed per call, not once here: signing in and
        # loading the page takes longer than `IDLE_SECONDS`, so a fixed
        # timestamp would be stale by the time the first poll ran, the other
        # tab would be evicted as abandoned, and this page would update. That
        # is correct behaviour for an abandoned tab and the wrong thing to
        # assert here - it is covered by the unit tests instead.
        client.zrange.side_effect = lambda *args, **kwargs: [
            (b"OTHERADDRESS", _time.time())
        ]
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = client

        self.sign_in()
        self.open_page()
        before = self.band()
        self.arm()
        self.browser.execute_script("window.__stillHere = true;")

        # Long enough for several polls at LIVEREFRESH_POLL_SECONDS.
        _time.sleep(10)

        assert self.band() == before
        assert self.browser.execute_script("return window.__stillHere;") is True

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_reader_who_did_not_opt_in_polls_nothing(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """The tier buys the choice; the setting is the reader taking it.

        Asserted on the marker rather than on the absence of an update,
        because "nothing happened yet" and "nothing will ever happen" look
        identical for the first few seconds.
        """
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        mocked_redis.return_value = self._redis()

        self.sign_in(live_refresh=False)
        self.open_page()

        assert self.browser.find_elements(By.ID, "id-liverefresh") == []

    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_reader_below_the_band_now_gets_the_free_taste(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """**This asserted the opposite until the allowance existed.**

        Below Asastatser the marker was withheld entirely, so an Intro reader
        polled nothing. They now get a daily allowance, and a reader with no
        marker could never spend it - so the marker is rendered and the limit is
        enforced per poll instead.

        The entitlement is still re-asked on every render rather than trusted
        from the profile; what changed is the answer, not where it comes from.
        """
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": INTRO}
        mocked_redis.return_value = self._redis()

        self.sign_in(live_refresh=True, permission=INTRO)
        self.open_page()

        assert self.browser.find_elements(By.ID, "id-liverefresh") != []

    @mock.patch("widgets.inhouse.liverefresh.views.spend")
    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_spent_reader_is_handed_back_to_the_free_reload(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis,
        mocked_spend,
    ):
        """**The handover, which is the whole reason this is not a 204.**

        A page that simply stopped would leave them with neither the live
        updates nor the sixty-second reload a non-subscriber gets - worse than
        never having had it, and indistinguishable from a broken feature.
        `address.js` stands its own timer down whenever the marker is present
        and asks every tick, so taking the marker off *is* the handover.
        """
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": INTRO}
        mocked_redis.return_value = self._redis()
        mocked_spend.return_value = -1.0

        self.sign_in(live_refresh=True, permission=INTRO)
        self.open_page()
        self.arm()

        self.wait_until(
            lambda: self.browser.find_elements(By.ID, "id-liverefresh") == [],
            timeout=15,
        )

        notice = self.browser.find_element(By.ID, "id-liverefresh-spent")
        assert notice.is_displayed()
        # **The wording is the product.** A reader who is told only that
        # something stopped has been told the least useful half of it: they need
        # to know the page still updates, that the allowance comes back on its
        # own, and what removes the limit.
        text = notice.text.lower()
        assert "sixty-second" in text or "slower" in text
        assert "week" in text
        assert notice.find_elements(By.TAG_NAME, "a") != []

    @mock.patch("widgets.inhouse.liverefresh.views.spend")
    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_reader_is_shown_what_is_left(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis,
        mocked_spend,
    ):
        """**An allowance nobody can see is one that only ever surprises them.**

        The badge ships hidden in the non-cached partial - the address page is
        cached across readers, so a balance rendered into it would show whoever
        warmed the entry to everybody else - and the script reveals it and moves
        it beside the control once a poll answers.
        """
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": INTRO}
        mocked_redis.return_value = self._redis()
        mocked_spend.return_value = 7080.0

        self.sign_in(live_refresh=True, permission=INTRO)
        self.open_page()
        self.arm()

        self.wait_until(
            lambda: self.browser.find_element(
                By.ID, "id-liverefresh-left"
            ).is_displayed(),
            timeout=15,
        )
        badge = self.browser.find_element(By.ID, "id-liverefresh-left")
        # Hours and minutes, not a second count: it is an allowance, and a
        # number ticking beside a page that already updates every block is two
        # things moving for no reason.
        assert "1h 58m" in badge.text


class LiveRefreshClassicTest(LiveRefreshTest):
    """The same feature on the layout most readers are actually on.

    `address.html` renders a different band - a `.tooltip` wrapper around the
    figure, plus an sr-only span repeating the USD line - and a row value with
    the unit *inside* the span rather than beside it. So the fragments differ in
    what they render as well as in what they address, and the widget branches on
    the reader's layout to pick a set.

    Inherited wholesale on purpose: every test in the parent class runs again
    against classic markup, because the question each one asks is the same and
    the answers are what differ. What is overridden is only how a reader is
    signed in and what says the page has finished loading.
    """

    #: `address.html` has no position rows; the breakdown is design 2/3 only.
    RENDERS_POSITIONS = False

    def sign_in(self, live_refresh=True, permission=ASASTATSER):
        """Log a reader in on the classic layout rather than the dynamic one."""
        cookie = self.create_session_cookie(
            username="live@example.com", password="top_secret", permission=permission
        )
        profile = get_user_model().objects.get(username="live@example.com").profile
        profile.preferred_layout = "classic"
        profile.live_refresh = live_refresh
        profile.save()
        self.browser.get(self.server_url + COOKIE_SEED_URL)
        self.browser.add_cookie(cookie)

    def open_page(self):
        """Load the address page and wait for the classic band.

        The parent waits on `window.asastatsToolbar`, which is the dynamic
        layout's toolbar and never initialises here.
        """
        self.record_javascript_errors()
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.wait_until(
            lambda: self.browser.execute_script(
                "return !!document.getElementById('id-band-classic');"
            )
        )

    BAND_DATA = "#id-band-classic .pricetip"

    def value_text(self, figure):
        """Classic keeps ALGO inside the value span rather than in a sibling."""
        return f"{figure} ALGO"

    def band(self):
        """Return the total the classic band is showing.

        The figure lives in `.pricetip` *inside* the `.tooltip` wrapper, which
        is the element swapped out of band - so reading the wrapper's text would
        pass whether or not the swap reached the figure.
        """
        return self.browser.execute_script(
            "var el = document.querySelector('#id-band-classic .pricetip');"
            "return el && el.textContent.trim();"
        )
