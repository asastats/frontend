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
#: The same holdings after the account transacted: the counter has stepped,
#: which is what a block naming the account does, and the asset set has not
#: changed - the case a fragment cannot express and a reload must.
MOVED_FINGERPRINT = "8:abc123def456"


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

    def _published(self, values=None, holdings=RENDERED_FINGERPRINT):
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
                "round": 64595872,
            }
        )

    def _redis(self, values=None, holdings=RENDERED_FINGERPRINT):
        """A client that answers with one published block and records the beat."""
        client = mock.MagicMock()
        client.get.return_value = self._published(values, holdings)
        return client

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

    @mock.patch("widgets.inhouse.liverefresh.views.remaining")
    @mock.patch("widgets.inhouse.liverefresh.views.redis_instance")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_spent_reader_is_handed_back_to_the_free_reload(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis,
        mocked_remaining,
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
        mocked_remaining.return_value = -1.0

        self.sign_in(live_refresh=True, permission=INTRO)
        self.open_page()
        self.arm()

        self.wait_until(
            lambda: self.browser.find_elements(By.ID, "id-liverefresh") == [],
            timeout=15,
        )

        notice = self.browser.find_element(By.ID, "id-liverefresh-spent")
        assert notice.is_displayed()


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
