"""Testing module for :py:mod:`api.live` module."""

import msgpack
import pytest

from api import live
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from utils.tests.fixtures import TEST_ADDRESS, TEST_ADDRESS2

ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
PROFESSIONAL = SUBSCRIPTION_TIER_PERMISSIONS["Professional"]
CLUSTER = SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]


def _warm(mocker, admitted, evicted=None):
    """Stand in for the widgets repo's warm-set module and manifest.

    Patched through `_warm_set` rather than as a module attribute, because
    `api.live` deliberately does not hold one - see `_warm_set`.
    """
    warmset = mocker.MagicMock()
    warmset.touch.return_value = (admitted, evicted or [])
    warmset.cap_for.return_value = 5
    mocker.patch.object(live, "_warm_set", return_value=(warmset, mocker.MagicMock()))
    return warmset


@pytest.fixture(autouse=True)
def _enabled(settings):
    """These tests are about the gates below the switch, so it is on.

    The switch itself is asserted by `TestApiLiveSubscribingEnabled`, which is
    the one place that must see it off.
    """
    settings.API_LIVE_ENABLED = True
    settings.API_LIVE_SHARED_TOKEN_USER_IDS = frozenset()


class TestApiLiveSubscribingEnabled:
    """Testing class for :py:func:`api.live.subscribing_enabled`."""

    def test_api_live_subscribing_is_off_unless_switched_on(self, settings, mocker):
        """**This is how it ships.**

        Everything else here costs a Redis round trip; subscribing costs the
        engine a re-price every block for as long as the caller keeps asking,
        and it starts the instant an entitled caller makes a request.
        """
        settings.API_LIVE_ENABLED = False
        client = mocker.MagicMock()

        assert live.subscribing_enabled() is False
        assert live.subscribe(TEST_ADDRESS, "", 7, CLUSTER, client=client) is False
        client.zadd.assert_not_called()


class TestApiLiveSharedToken:
    """Testing class for :py:func:`api.live.is_shared_token`."""

    def test_api_live_a_shared_token_never_subscribes(self, settings, mocker):
        """**A per-account limit measures a person; this is a population.**

        The mobile app ships one credential for its whole installed base. Tier
        is the wrong gate for it - account 24 is Professional and would pass -
        so the rule `RUN-mobile-token-swap.md` states in prose is here in code:
        the app stays on the cached path and never subscribes.
        """
        settings.API_LIVE_SHARED_TOKEN_USER_IDS = frozenset({24})
        client = mocker.MagicMock()
        _warm(mocker, [TEST_ADDRESS])

        assert live.subscribe(TEST_ADDRESS, "", 24, CLUSTER, client=client) is False
        client.zadd.assert_not_called()

    def test_api_live_a_person_on_the_same_tier_still_subscribes(self, settings, mocker):
        """The exclusion is about the credential, not the entitlement."""
        settings.API_LIVE_SHARED_TOKEN_USER_IDS = frozenset({24})
        client = mocker.MagicMock()
        _warm(mocker, [TEST_ADDRESS])

        assert live.subscribe(TEST_ADDRESS, "", 25, CLUSTER, client=client) is True

    def test_api_live_shared_token_list_is_empty_by_default(self):
        """An exclusion nobody has filled in must not silently exclude."""
        assert live.is_shared_token(1) is False


class TestApiLiveWarmSetImport:
    """Testing class for :py:func:`api.live._warm_set`."""

    def test_api_live_a_missing_warm_set_does_not_break_the_import(self, mocker):
        """**This took the whole site down on 2026-09-20.**

        `warmset` lives in the widgets repo, which syncs separately from this
        one, so "frontend newer than widgets" is an ordinary state for minutes
        at a time. Imported at module scope it made `api.views` unimportable,
        then `config/urls.py`, and every page on the site 500d - for a feature
        that was switched off.
        """
        mocker.patch.dict("sys.modules", {"widgets.inhouse.liverefresh": None})

        assert live._warm_set() == (None, None)

    def test_api_live_warm_set_returns_the_real_widget_module(self):
        """**The success path, which every other test here patches away.**

        The rest either force the ImportError or replace `_warm_set` wholesale,
        so nothing was actually importing the widget - and an import that
        silently stopped resolving would have looked exactly like a passing
        suite while the feature quietly refused every subscription in
        production.

        Asserts the objects are usable rather than merely non-None: the cap and
        the touch are what `subscribe` calls on them.
        """
        warmset, manifest = live._warm_set()

        assert callable(warmset.touch)
        assert callable(warmset.cap_for)
        assert manifest.required_permission

    def test_api_live_warm_set_agrees_with_the_widgets_own_bands(self):
        """One warm set per reader spans browser and API, so the cap this
        module resolves has to be the number the widget itself would use."""
        from widgets.inhouse.liverefresh import warmset as widget_warmset
        from widgets.inhouse.liverefresh.manifest import MANIFEST

        warmset, manifest = live._warm_set()

        assert warmset is widget_warmset
        assert manifest is MANIFEST

    def test_api_live_subscribe_refuses_without_a_warm_set(self, mocker):
        """No cap can be applied, so nothing is subscribed: an unbounded warm
        set is a worse answer than a cached one."""
        client = mocker.MagicMock()
        mocker.patch.object(live, "_warm_set", return_value=(None, None))

        assert live.subscribe(TEST_ADDRESS, "", 7, CLUSTER, client=client) is False
        client.zadd.assert_not_called()


class TestApiLiveWantsBlockTime:
    """Testing class for :py:func:`api.live.wants_block_time`."""

    @pytest.mark.parametrize(
        "permission,expected",
        [
            (0, False),
            (ASASTATSER, False),
            (PROFESSIONAL, True),
            (CLUSTER, True),
        ],
    )
    def test_api_live_wants_block_time_by_tier(self, permission, expected):
        """**Asastatser is deliberately not a block-time tier.**

        It keeps the 60-second cached path it has today. Professional and
        Cluster are what block-time was sold with, and `api/tiers.py` records
        that freshness enters its table only when something serves it.
        """
        assert live.wants_block_time(permission) is expected


class TestApiLivePageKey:
    """Testing class for :py:func:`api.live.page_key`."""

    def test_api_live_page_key_is_the_address_for_a_single(self):
        assert live.page_key(TEST_ADDRESS, "") == TEST_ADDRESS

    def test_api_live_page_key_is_rederived_for_a_bundle(self):
        """**An old bookmark carries a pre-sort hash.**

        The engine publishes under the canonical hash, so a key taken from the
        path would miss the snapshot entirely for exactly the visitors whose
        bundle URLs are oldest.
        """
        addresses = f"{TEST_ADDRESS} {TEST_ADDRESS2}"
        assert live.page_key("ancientbookmarkhash", addresses) != ("ancientbookmarkhash")
        assert live.page_key("ancientbookmarkhash", addresses) == live.page_key(
            "", f"{TEST_ADDRESS2} {TEST_ADDRESS}"
        )


class TestApiLiveSubscribe:
    """Testing class for :py:func:`api.live.subscribe`."""

    def test_api_live_subscribe_refuses_a_tier_without_block_time(self, mocker):
        """Nothing is written for a caller who was not sold this."""
        client = mocker.MagicMock()

        assert live.subscribe(TEST_ADDRESS, "", 7, ASASTATSER, client=client) is False
        client.zadd.assert_not_called()

    def test_api_live_subscribe_refuses_without_a_reader(self, mocker):
        """The cap is per account, so an unidentified caller cannot hold one."""
        client = mocker.MagicMock()

        assert (
            live.subscribe(TEST_ADDRESS, "", None, PROFESSIONAL, client=client) is False
        )
        client.zadd.assert_not_called()

    def test_api_live_subscribe_writes_both_sets(self, mocker):
        """`lvx` is what the pass re-prices; `lva` is what it snapshots.

        Two keys because the browser wants only the first: a watched tab costs
        a re-price and a 170-byte diff, and must not also cost a serialized
        account nobody reads.
        """
        client = mocker.MagicMock()
        _warm(mocker, [TEST_ADDRESS])

        assert (
            live.subscribe(TEST_ADDRESS, "", 7, PROFESSIONAL, client=client, now=100.0)
            is True
        )

        written = dict(call.args for call in client.zadd.call_args_list)
        assert written[live.SUBSCRIBED_KEY] == {TEST_ADDRESS: 100.0}
        assert written[live.API_WARM_KEY] == {TEST_ADDRESS: 100.0}

    def test_api_live_subscribe_keys_lvx_by_addresses_and_lva_by_page(self, mocker):
        """**The two sets are keyed differently, and mixing them up is silent.**

        `lvx` members are address strings, because that is what the widget
        writes and what `_live_pages` normalises and splits. `lva` is keyed by
        page, because `_live_page` tests membership after it has resolved the
        bundle to its hash. A bundle written the wrong way round into either
        one is simply never matched, and nothing reports it.
        """
        client = mocker.MagicMock()
        addresses = f"{TEST_ADDRESS} {TEST_ADDRESS2}"
        _warm(mocker, [TEST_ADDRESS, TEST_ADDRESS2])

        live.subscribe("thehash", addresses, 7, CLUSTER, client=client, now=100.0)

        written = dict(call.args for call in client.zadd.call_args_list)
        assert written[live.SUBSCRIBED_KEY] == {addresses: 100.0}
        assert written[live.API_WARM_KEY] == {live.page_key("thehash", addresses): 100.0}

    def test_api_live_subscribe_refuses_a_bundle_that_did_not_resolve(self, mocker):
        """A hash with no addresses must reach neither set.

        `addresses` is empty for a single address *and* for a bundle nobody can
        resolve, so `addresses or value` wrote the hash into `lvx` - where the
        pass fetches it as an account and raises on every block. See
        docs/logbook.md.
        """
        client = mocker.MagicMock()
        _warm(mocker, [TEST_ADDRESS])

        assert (
            live.subscribe(
                "6F50FC1B2C3D4E5F60718293A4B5C6D7E8F90A1B",
                "",
                7,
                CLUSTER,
                client=client,
                now=100.0,
            )
            is False
        )
        client.zadd.assert_not_called()

    def test_api_live_subscribe_still_takes_a_single_address(self, mocker):
        """The guard above must not read a bare address as an unresolved hash."""
        client = mocker.MagicMock()
        _warm(mocker, [TEST_ADDRESS])

        assert (
            live.subscribe(TEST_ADDRESS, "", 7, CLUSTER, client=client, now=100.0) is True
        )

        written = dict(call.args for call in client.zadd.call_args_list)
        assert written[live.SUBSCRIBED_KEY] == {TEST_ADDRESS: 100.0}

    def test_api_live_subscribe_charges_the_addresses_not_the_page(self, mocker):
        """The warm set counts addresses, which is what makes it a union.

        A reader with `{A,B,C}` open in a browser and an API call for `{C,D}`
        has a warm set of four, not five. Charging the bundle as one member
        would bill `C` twice and make the two surfaces incomparable.
        """
        client = mocker.MagicMock()
        touch = _warm(mocker, [TEST_ADDRESS, TEST_ADDRESS2]).touch

        live.subscribe(
            "thehash",
            f"{TEST_ADDRESS} {TEST_ADDRESS2}",
            7,
            CLUSTER,
            client=client,
            now=100.0,
        )

        assert touch.call_args.args[1] == [TEST_ADDRESS, TEST_ADDRESS2]
        assert touch.call_args.kwargs["evict"] is False

    def test_api_live_subscribe_writes_nothing_when_over_the_cap(self, mocker):
        """**Refused whole, and not an error.**

        Half a bundle kept warm is a response where some rows are block-fresh
        and others a minute old with nothing saying which - the partial
        freshness that ruled out overlaying the diff in the first place. Over
        the cap the caller still gets the cached answer.
        """
        client = mocker.MagicMock()
        _warm(mocker, [])

        assert live.subscribe(TEST_ADDRESS, "", 7, CLUSTER, client=client) is False
        client.zadd.assert_not_called()

    def test_api_live_subscribe_survives_an_unreachable_redis(self, mocker):
        """The API must not 500 because the live feature is down."""
        client = mocker.MagicMock()
        client.zadd.side_effect = RuntimeError("connection refused")
        _warm(mocker, [TEST_ADDRESS])

        assert live.subscribe(TEST_ADDRESS, "", 7, CLUSTER, client=client) is False


class TestApiLiveSnapshot:
    """Testing class for :py:func:`api.live.snapshot`."""

    @staticmethod
    def _published(mocker, account=None, holdings=None):
        """A client answering the one MGET this module makes."""
        client = mocker.MagicMock()
        client.mget.return_value = [
            None if account is None else msgpack.packb(account),
            holdings,
        ]
        return client

    def test_api_live_snapshot_returns_the_published_account(self, mocker):
        """**`lvn:` holds an account and nothing else.** This is what an
        entitled caller is served, so its shape is a contract an engine deploy
        must not be able to change - the fingerprint the browser's widget needs
        lives in a key beside it rather than wrapped around this one."""
        client = self._published(mocker, {"total": {"total": 1.0}})

        assert live.snapshot(TEST_ADDRESS, "", client=client) == {"total": {"total": 1.0}}
        client.mget.assert_called_once_with(
            f"{live.SNAPSHOT_PREFIX}:{TEST_ADDRESS}",
            f"{live.SNAPSHOT_HOLDINGS_PREFIX}:{TEST_ADDRESS}",
        )

    def test_api_live_stamped_snapshot_carries_the_fingerprint(self, mocker):
        """The widget writes this back onto the page as what it has caught up
        to, so it has to be the fingerprint of *this* account rather than of
        whatever was published most recently."""
        client = self._published(mocker, {"total": {}}, b"8:assets:positions")

        assert live.stamped_snapshot(TEST_ADDRESS, "", client=client) == (
            {"total": {}},
            "8:assets:positions",
        )

    def test_api_live_stamped_snapshot_reads_an_absent_stamp_as_unknown(self, mocker):
        """An engine that predates `lvnh:` leaves it absent. Empty is "cannot
        tell", and the caller falls back to the reload rather than claiming the
        page has caught up to something it has not."""
        client = self._published(mocker, {"total": {}}, None)

        assert live.stamped_snapshot(TEST_ADDRESS, "", client=client) == (
            {"total": {}},
            "",
        )

    def test_api_live_snapshot_reads_integer_keyed_maps(self, mocker):
        """msgpack refuses integer keys unless told not to, and these
        structures are keyed by asset id."""
        client = self._published(mocker, {"values": {31566704: 2.5}})

        assert live.snapshot(TEST_ADDRESS, "", client=client) == {
            "values": {31566704: 2.5}
        }

    def test_api_live_snapshot_is_none_before_the_first_block(self, mocker):
        """**Every first request of a subscription lands here.**

        The page is not warm until a block has passed over it, so the caller's
        first answer is the cached one and every one after it is fresh. A
        caller that never subscribes stays on this path forever.
        """
        client = self._published(mocker, None, "8:assets:positions")

        assert live.snapshot(TEST_ADDRESS, "", client=client) is None

    def test_api_live_snapshot_survives_an_undecodable_payload(self, mocker):
        """Falls back to the engine rather than serving half an account."""
        client = mocker.MagicMock()
        client.mget.return_value = [b"\xff\xfe not msgpack", None]

        assert live.snapshot(TEST_ADDRESS, "", client=client) is None

    def test_api_live_snapshot_survives_an_unreachable_redis(self, mocker):
        client = mocker.MagicMock()
        client.mget.side_effect = RuntimeError("connection refused")

        assert live.snapshot(TEST_ADDRESS, "", client=client) is None
