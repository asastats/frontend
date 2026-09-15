"""The address page updating itself from the engine's published block.

Everything under this feature is covered by unit tests - the engine's diff, the
widget's fragments, the timer in `address.js` - and none of it answers the
question the feature exists for: does the page change under a reader without
taking anything away from them?

That is a browser question and only a browser can answer it. The two halves
that matter here are **the page must not reload** (a reload is what the free
tier does, and the whole point of the subscriber path is that it does not) and
**what the reader had open must survive**. A poll that swapped the right figures
while closing an open row would pass every test in this repo except these.
"""

import json
import os
from unittest import mock

import msgpack
from django.contrib.auth import get_user_model
from django.core.cache import cache
from selenium.webdriver.common.by import By
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

    def _published(self, values=None):
        """Return a msgpack block as the engine's pass publishes one."""
        total = self.sample["total"]
        return msgpack.packb(
            {
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

    def _redis(self, values=None):
        """A client that answers with one published block and records the beat."""
        client = mock.MagicMock()
        client.get.return_value = self._published(values)
        return client

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
                "return el && el.textContent.trim() === '99.50';",
                asset_id,
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
            "var el = document.getElementById('id-band-total');"
            "return {price: el.dataset.price, pricealgo: el.dataset.pricealgo,"
            "        total: el.dataset.total, totalwnft: el.dataset.totalwnft,"
            "        totalnft: el.dataset.totalnft};"
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
    def test_a_reader_below_the_band_polls_nothing(
        self, mocked_fetch, mocked_status, mocked_capabilities, mocked_redis
    ):
        """Opted in and then the tier lapsed. The setting outlives the
        entitlement, so the gate has to be re-asked on every render rather than
        trusted from the profile."""
        mocked_fetch.return_value = self.sample
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": INTRO}
        mocked_redis.return_value = self._redis()

        self.sign_in(live_refresh=True, permission=INTRO)
        self.open_page()

        assert self.browser.find_elements(By.ID, "id-liverefresh") == []
