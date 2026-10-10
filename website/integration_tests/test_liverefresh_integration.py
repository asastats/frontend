"""Integration tests for the Real-time refresh widget against a real Redis.

**The largest cross-project surface of any widget here, and until now no
integration test at all.** This widget writes two keys the engine reads and
reads one the engine writes:

* ``lvx`` - which pages to re-price, scored by the moment a poll was served
* ``lvq`` - which of those a paying reader has open, so a free reader's page is
  shed first when the block budget runs out
* ``lvp:{page}`` - what the pass published, msgpack, read back here

Everything about those three is asserted in the unit suite against a
``MagicMock``, which agrees with whatever it is told. What is tested below is
the half nothing else can see: that a key this widget writes is a key the engine
can find, and that a payload the engine wrote is one this widget can read.

**The engine's own read is reproduced literally**, from
``engine/utils/cache.py``::

    oldest = now - LIVE_SUBSCRIPTION_SECONDS
    members = cache_client.zrangebyscore(CACHE_KEY_LIVE_SUBSCRIBED, oldest, "+inf")

so the ageing is asserted the way the engine ages it rather than the way this
widget imagines it does. Ninety seconds is the engine's number and it is named
here for the same reason the alerts suite names the history tick: this file
exists to state a contract, and importing it from one side would mean only one
side has to keep it.

**On the page key**, which is the trap this widget has already been caught by.
The pass publishes under ``bundle_from_addresses(addresses) if " " in addresses
else addresses`` - the raw address when there is one, the hash when there are
several. Hashing unconditionally asked for a key nothing writes, and the failure
had the worst possible shape: the poll still ran, still heartbeated, so the
engine went on re-pricing the page every block while every response was a 204.
A live indicator over a page that never moved, and nothing logged. The first
test below is that.

**On the database.** Db 15, as the alerts suite uses, with only the keys these
tests wrote removed afterwards. ``lvx`` and ``lvq`` are live production sets on
db 0 - a test that heartbeated into them would ask the engine to re-price a page
that does not exist.
"""

import time
import uuid

import msgpack
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from redis import Redis

from api.live import API_WARM_KEY, SNAPSHOT_PREFIX, page_key, snapshot, subscribe
from api.tiers import block_time
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from walletauth.models import LinkedAddress
from widgets.inhouse.liverefresh.views import (
    BACKLOG_PREFIX,
    PAID_KEY,
    PAYLOAD_PREFIX,
    SUBSCRIBED_KEY,
)

#: The database these tests own. See the module docstring.
TEST_REDIS_DB = 15

#: The engine's window on `lvx` and `lvq`, from its `LIVE_SUBSCRIPTION_SECONDS`.
#:
#: **A crashed Daphne never gets to say goodbye**, which is why expiry is a
#: score range on the reader's side rather than a delete on ours.
SUBSCRIPTION_SECONDS = 90

#: A real address, so the URL pattern matches and the page key is the raw one.
ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"


def _client():
    """Return a client on the database these tests own."""
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT_LOCAL,
        db=TEST_REDIS_DB,
        password=settings.REDIS_AUTH,
    )


def _engine_reads_subscriptions(client, key, now=None):
    """Return the live members of `key`, exactly as the engine reads them.

    Copied from ``cached_live_subscriptions``. Stale members are left in place
    deliberately on that side - trimming them would be a write from a process
    that only reads, on a key another service owns - so "is this page live" is a
    score range and nothing else.

    :param client: an open Redis client
    :param key: `lvx` or `lvq`
    :type key: str
    :param now: unix time to judge staleness against
    :type now: float
    :return: list of str
    """
    oldest = (time.time() if now is None else now) - SUBSCRIPTION_SECONDS
    return [
        member.decode() if isinstance(member, bytes) else member
        for member in client.zrangebyscore(key, oldest, "+inf")
    ]


def _reader(email, tier="Professional", linked=True):
    """Return a signed-up reader at `tier`, with ADDRESS linked."""
    user = get_user_model().objects.create_user(username=email, email=email, password="x")
    profile = user.profile
    profile.permission = SUBSCRIPTION_TIER_PERMISSIONS[tier]
    profile.address = ADDRESS
    profile.save()
    if linked:
        LinkedAddress.objects.create(
            profile=profile,
            address=ADDRESS,
            canonical_address=ADDRESS,
            chain="algorand",
            auth_method="algorand_wallet",
            is_primary=True,
            login_enabled=True,
        )
    return user


@override_settings(REDIS_DB=TEST_REDIS_DB)
class LiveRefreshRedisContractTest(TestCase):
    """The three keys, against a real server."""

    def setUp(self):
        """Note what is here, so afterwards only what a poll added is removed."""
        super().setUp()
        self.redis = _client()
        self.payload_key = f"{PAYLOAD_PREFIX}:{ADDRESS}"
        self.redis.zrem(SUBSCRIBED_KEY, ADDRESS)
        self.redis.zrem(PAID_KEY, ADDRESS)
        # **A snapshot rather than a list of prefixes.** One poll writes more
        # than the three keys this file is about - a warm set at `lvw:{reader}`,
        # an allowance bucket at `lvf:…`, and a bundle mapping under its own
        # hash with no TTL at all. Enumerating those means this cleanup drifts
        # the first time one of them is renamed, and the failure is silent: a
        # test database that fills up.
        #
        # Safe because it removes only keys that were absent when this test
        # began, on a database these tests own. It is never a `flushdb`.
        self.before = set(self.redis.scan_iter(count=1000))
        self.addCleanup(self._forget)
        self.client = Client()

    def _forget(self):
        """Remove the keys this test caused to exist, and its two members.

        `lvx` and `lvq` are whole keys rather than per-test ones, so the members
        are removed by name - never the key.
        """
        self.redis.zrem(SUBSCRIBED_KEY, ADDRESS)
        self.redis.zrem(PAID_KEY, ADDRESS)
        added = set(self.redis.scan_iter(count=1000)) - self.before
        if added:
            self.redis.delete(*added)

    def _publish(self, total=1234.5):
        """Write a payload under the key the pass would use for one address."""
        self.redis.set(
            self.payload_key,
            msgpack.packb({"total": total, "priceusdc": 0.25, "values": {}}),
            ex=120,
        )

    def _poll(self, user):
        """Serve one poll as the widget's own JavaScript would."""
        self.client.force_login(user)
        return self.client.get(
            reverse("liverefresh", args=[ADDRESS]), HTTP_HX_REQUEST="true"
        )

    def test_liverefresh_integration_one_address_is_keyed_by_itself(self):
        """**The trap that produced a live indicator over a static page.**

        The pass publishes under the raw address when there is one and the hash
        when there are several. A poll that looked under a hash of the single
        address found nothing, answered 204 every block, and went on
        heartbeating - so the engine kept re-pricing a page whose reader was
        told nothing had changed.
        """
        self._publish()
        user = _reader("lr-key@example.com")

        response = self._poll(user)

        assert (
            response.status_code == 200
        ), "the poll could not find the payload the pass published"

    def test_liverefresh_integration_nothing_published_is_a_204(self):
        """**204 rather than an empty body**: htmx leaves the page alone, so a
        block that moved nothing costs one request and no DOM work."""
        user = _reader("lr-empty@example.com")

        response = self._poll(user)

        assert response.status_code == 204

    def test_liverefresh_integration_a_poll_is_visible_to_the_engine(self):
        """`lvx` is how the engine learns a page is being read at all.

        Asserted through the engine's own score range rather than by looking
        for the member: a page written with a score the engine's window does
        not cover is a page it will never re-price, and the membership test
        would pass anyway.
        """
        self._publish()
        user = _reader("lr-heartbeat@example.com")

        self._poll(user)

        assert ADDRESS in _engine_reads_subscriptions(self.redis, SUBSCRIBED_KEY)

    def test_liverefresh_integration_a_stale_poll_falls_out_of_the_window(self):
        """Ninety seconds after the last poll the page stops being re-priced.

        Expiry is the reader's job by construction: a crashed Daphne never gets
        to say goodbye, so the engine judges by score and nothing has to be
        deleted on the way out.
        """
        self._publish()
        user = _reader("lr-stale@example.com")
        self._poll(user)

        later = time.time() + SUBSCRIPTION_SECONDS + 1

        assert ADDRESS not in _engine_reads_subscriptions(
            self.redis, SUBSCRIBED_KEY, now=later
        )

    def test_liverefresh_integration_a_paying_reader_is_marked_paid(self):
        """`lvq` is what lifts a page over the engine's admission budget.

        Marked before the payload is looked at, deliberately: a page that is
        not admitted is never published, so deciding this on whether something
        had been published would make a shed page's shedding permanent.
        """
        user = _reader("lr-paid@example.com", tier="Professional")

        self._poll(user)

        assert ADDRESS in _engine_reads_subscriptions(self.redis, PAID_KEY)

    def test_liverefresh_integration_a_free_reader_is_not(self):
        """Asking the engine to prioritise a page nobody is paying for would
        spend a subscriber's capacity on somebody else's tab."""
        user = _reader("lr-free@example.com", tier="Intro")

        self._poll(user)

        assert ADDRESS not in _engine_reads_subscriptions(self.redis, PAID_KEY)

    def test_liverefresh_integration_the_member_is_the_page_the_engine_expects(
        self,
    ):
        """`zadd` and `zrange` have to agree about encoding.

        The engine decodes each member and looks up `lvp:{member}`; a member
        that comes back as anything other than the page string is a page it
        cannot find.
        """
        self._publish()
        user = _reader("lr-member@example.com")

        self._poll(user)

        members = self.redis.zrange(SUBSCRIBED_KEY, 0, -1)
        assert ADDRESS.encode() in members

    def test_liverefresh_integration_a_payload_the_engine_wrote_is_read(self):
        """The msgpack shape, end to end through the real view.

        The pass keys `values` by asset id as an *integer*; unpacking without
        `strict_map_key=False` raises, and unpacking into strings would silently
        render a page of nothing.
        """
        self.redis.set(
            self.payload_key,
            msgpack.packb({"total": 42.0, "priceusdc": 0.25, "values": {31566704: 7.25}}),
            ex=120,
        )
        user = _reader("lr-payload@example.com")

        response = self._poll(user)

        assert response.status_code == 200

    def test_liverefresh_integration_a_payload_that_aged_out_is_not_charged(self):
        """**Nothing published, so nothing is charged.**

        The case that made this a bug rather than an edge: on 2026-09-16 the
        overnight rotation shed 528 of 978 wanted pages at once, their payloads
        aged out of the 120 s TTL behind them, and every reader of one was being
        billed wall-clock seconds for a page that could not move.
        """
        self._publish()
        user = _reader("lr-aged@example.com", tier="Intro")
        self._poll(user)
        self.redis.delete(self.payload_key)

        response = self._poll(user)

        assert response.status_code == 204


#: A floor move on one collection the account holds, as the engine's
#: `_floor_events` makes it for the block that carries it.
FLOOR_MOVE = {
    "kind": "floor",
    "round": 41234567,
    "collection": "coll-a",
    "name": "Pixel",
    "old": 2.0,
    "new": 2.5,
    "held": 3,
    "algo": 1.5,
}


def _dynamic_reader(email):
    """Return a reader on the dynamic layout, the one the charts-side log was built for."""
    user = _reader(email)
    user.profile.preferred_layout = "dynamic"
    user.profile.save()
    return user


def _block(seq, events=(), total=1234.5):
    """Return one payload as the engine's pass publishes it, msgpack packed."""
    return msgpack.packb(
        {
            "seq": seq,
            "total": total,
            "priceusdc": 0.25,
            "values": {},
            "events": list(events),
        }
    )


@override_settings(REDIS_DB=TEST_REDIS_DB)
class LiveLogRedisContractTest(TestCase):
    """Floor-move events for the live log, against a real server.

    The engine writes the latest payload under `lvp:{page}` and the last
    twenty under `lvl:{page}`, newest first. The widget reads both, so a row
    reaches a tab that is at the latest block and also one that missed it.
    """

    def setUp(self):
        """Note what is here, so afterwards only what these tests added is removed."""
        super().setUp()
        self.redis = _client()
        self.payload_key = f"{PAYLOAD_PREFIX}:{ADDRESS}"
        self.backlog_key = f"{BACKLOG_PREFIX}:{ADDRESS}"
        self.redis.zrem(SUBSCRIBED_KEY, ADDRESS)
        self.redis.zrem(PAID_KEY, ADDRESS)
        # The same snapshot cleanup as LiveRefreshRedisContractTest, for the
        # same reason: one poll writes more keys than these tests name.
        self.before = set(self.redis.scan_iter(count=1000))
        self.addCleanup(self._forget)
        self.client = Client()

    def _forget(self):
        """Remove the members these tests added and every key they created."""
        self.redis.zrem(SUBSCRIBED_KEY, ADDRESS)
        self.redis.zrem(PAID_KEY, ADDRESS)
        added = set(self.redis.scan_iter(count=1000)) - self.before
        if added:
            self.redis.delete(*added)

    def _latest(self, block):
        """Publish `block` as the newest payload for the address."""
        self.redis.set(self.payload_key, block, ex=120)

    def _backlog(self, *newest_first):
        """Publish the backlog the engine keeps, newest first."""
        self.redis.delete(self.backlog_key)
        if newest_first:
            self.redis.rpush(self.backlog_key, *newest_first)

    def _poll(self, user, since=None):
        """Serve one poll as the widget would, optionally from a given `seq`."""
        self.client.force_login(user)
        url = reverse("liverefresh", args=[ADDRESS])
        if since is not None:
            url += f"?since={since}"
        return self.client.get(url, HTTP_HX_REQUEST="true")

    def test_liverefresh_integration_a_floor_move_is_written_as_a_log_row(self):
        """The row an engine block carries reaches the reader as an
        out-of-band row at the top of the log."""
        block = _block(1, [FLOOR_MOVE])
        self._latest(block)
        self._backlog(block)
        user = _dynamic_reader("ll-row@example.com")

        response = self._poll(user)

        body = response.content.decode()
        assert response.status_code == 200
        assert 'id="id-livelog-list" hx-swap-oob="afterbegin"' in body
        assert "Floor of Pixel from 2.00 to 2.50 ALGO" in body
        assert "+1.50 ALGO" in body

    def test_liverefresh_integration_a_tab_that_missed_the_block_still_gets_the_row(
        self,
    ):
        """**The block with the move was skipped, and the tab must not lose it.**

        The tab last applied seq 6. Seq 7 carried the move and seq 8 came after
        it, so the catch-up has to find seq 7 in the backlog and fold its row in.
        """
        latest = _block(8)
        self._latest(latest)
        self._backlog(latest, _block(7, [FLOOR_MOVE]), _block(6))
        user = _dynamic_reader("ll-missed@example.com")

        response = self._poll(user, since=6)

        assert response.status_code == 200
        assert "Floor of Pixel from 2.00 to 2.50 ALGO" in response.content.decode()

    def test_liverefresh_integration_a_tab_at_the_block_is_not_sent_the_row_again(
        self,
    ):
        """**A row is written once.** A tab that already applied the block that
        carried it gets the band and nothing for the log."""
        block = _block(8, [FLOOR_MOVE])
        self._latest(block)
        self._backlog(block)
        user = _dynamic_reader("ll-again@example.com")

        response = self._poll(user, since=8)

        assert response.status_code == 200
        assert "Floor of Pixel" not in response.content.decode()

    def test_liverefresh_integration_a_move_is_sent_when_the_total_has_not_moved(self):
        """**An event is news even when the account's total did not move.** A
        floor can change what a holding is worth without changing the total,
        so a 204 here would drop the row."""
        user = _dynamic_reader("ll-total@example.com")
        self._latest(_block(1))
        self._backlog(_block(1))
        self._poll(user)

        block = _block(2, [FLOOR_MOVE])
        self._latest(block)
        self._backlog(block, _block(1))
        response = self._poll(user, since=1)

        assert response.status_code == 200
        assert "Floor of Pixel" in response.content.decode()

    def test_liverefresh_integration_a_position_opened_is_written_as_a_log_row(self):
        """A position the engine saw open reaches the reader by name."""
        opened = {
            "kind": "position_open",
            "round": 41234568,
            "asset": 31566704,
            "name": "Mallow (ALGO down)",
            "provider": "Mallow",
            "value": 22.0,
        }
        block = _block(1, [opened])
        self._latest(block)
        self._backlog(block)
        user = _dynamic_reader("ll-open@example.com")

        response = self._poll(user)

        body = response.content.decode()
        assert "Opened Mallow (ALGO down) on Mallow" in body
        assert "+22.00 ALGO" in body

    def test_liverefresh_integration_a_position_closed_reaches_a_tab_that_missed_it(
        self,
    ):
        """**A close is named from the baseline, so a tab that skipped the block
        still sees which position went.**"""
        closed = {
            "kind": "position_close",
            "round": 41234569,
            "asset": 31566704,
            "name": "Mallow (ALGO down)",
            "provider": "Mallow",
            "value": 0.0,
        }
        latest = _block(4)
        self._latest(latest)
        self._backlog(latest, _block(3, [closed]), _block(2))
        user = _dynamic_reader("ll-closed@example.com")

        response = self._poll(user, since=2)

        assert "Closed Mallow (ALGO down) on Mallow" in response.content.decode()

    def test_liverefresh_integration_a_reload_restores_the_recent_rows(self):
        """**An asset bought reloads the page, and the reload must not lose its row.**

        The poll answers the holdings change with a reload and no body. The page
        that loads again renders its shell from the backlog the engine kept, so
        the row the reload was for is still there.
        """
        bought = {
            "kind": "asset_in",
            "round": 41234570,
            "asset": 31566704,
            "name": "Coin",
            "value": 7.5,
        }
        latest = _block(9)
        self._latest(latest)
        self._backlog(latest, _block(8, [bought]))
        user = _dynamic_reader("ll-restore@example.com")
        user.profile.live_refresh = True
        user.profile.save()
        self.client.force_login(user)

        response = self.client.get(reverse("swap_entry", args=[ADDRESS]))

        body = response.content.decode()
        assert response.status_code == 200
        assert 'id="id-livelog-list"' in body
        assert "Bought Coin" in body

    def test_liverefresh_integration_the_newest_rows_render_and_their_seq_with_them(self):
        """**The newest payload is rendered, not left to the first poll.**

        A block lands about every 2.8 s and the first poll comes 3 s after
        load, so a payload left to it was usually replaced before it was asked
        for. The shell names its `seq`, and the first poll asks only after it.
        """
        bought = {"kind": "asset_in", "round": 41234570, "asset": 31566704, "name": "Coin", "value": 7.5}
        online = {"kind": "online", "round": 41234571}
        latest = _block(9, [bought, online])
        self._latest(latest)
        self._backlog(latest, _block(8))
        user = _dynamic_reader("ll-newest@example.com")
        user.profile.live_refresh = True
        user.profile.save()
        self.client.force_login(user)

        body = self.client.get(reverse("swap_entry", args=[ADDRESS])).content.decode()

        assert 'data-log-seq="9"' in body
        assert 'id="id-livelog-copy"' in body
        assert '<li class="livelog-row" data-key="9.0">' in body
        assert "Bought Coin" in body
        assert "Account went online" in body
        # newest first: the online row came after the purchase in the block
        assert body.index("Account went online") < body.index("Bought Coin")

        url = reverse("liverefresh", args=[ADDRESS]) + "?logsince=9"
        response = self.client.get(url, HTTP_HX_REQUEST="true")
        assert "Bought Coin" not in response.content.decode()

    def test_liverefresh_integration_a_transfer_is_a_row_live_and_on_load(self):
        """**What the account's own transactions moved, as the engine publishes it.**"""
        sent = {
            "kind": "transfer",
            "round": 41234572,
            "asset": 0,
            "name": "ALGO",
            "amount": -2_500_000,
            "decimals": 6,
            "algo": -2.5,
            "usd": -0.5,
        }
        latest = _block(12, [sent])
        self._latest(latest)
        self._backlog(latest)
        user = _dynamic_reader("ll-transfer@example.com")

        live = self._poll(user).content.decode()

        assert "Sent 2.5000 ALGO" in live
        assert "-2.50 ALGO" in live
        user.profile.live_refresh = True
        user.profile.save()
        loaded = self.client.get(reverse("swap_entry", args=[ADDRESS])).content.decode()
        assert '<li class="livelog-row" data-key="12.0">' in loaded
        assert "Sent 2.5000 ALGO" in loaded

    def test_liverefresh_integration_liquidity_removed_is_one_row(self):
        """**One transaction group, one row**, as the engine publishes it."""
        removed = {
            "kind": "liquidity",
            "action": "removed",
            "round": 41234573,
            "pool": "Tinyman2 LP TALGO-TINY",
            "legs": [
                {"asset": 2537013734, "name": "tALGO", "amount": 32000609, "decimals": 6, "algo": 35.14},
                {"asset": 2200000000, "name": "TINY", "amount": 4536043332, "decimals": 6, "algo": 32.27},
            ],
            "algo": 67.41,
            "usd": 7.8,
            "ts": 1791615649,
        }
        latest = _block(13, [removed])
        self._latest(latest)
        self._backlog(latest)
        user = _dynamic_reader("ll-liquidity@example.com")

        body = self._poll(user).content.decode()

        assert body.count('class="livelog-row"') == 1
        assert "Removed liquidity, Tinyman2 LP TALGO-TINY: 32.0006 tALGO, 4,536.0433 TINY" in body

    def test_liverefresh_integration_an_nft_bought_is_restored_on_load(self):
        """An NFT purchase reloads the page like an asset does, so it restores the
        same way: the row is in the backlog, and the shell renders it."""
        bought = {
            "kind": "nft_in",
            "round": 41234571,
            "asset": 901,
            "name": "Pixel Punks",
            "value": 0.0,
        }
        latest = _block(11)
        self._latest(latest)
        self._backlog(latest, _block(10, [bought]))
        user = _dynamic_reader("ll-nft@example.com")
        user.profile.live_refresh = True
        user.profile.save()
        self.client.force_login(user)

        response = self.client.get(reverse("swap_entry", args=[ADDRESS]))

        assert "Bought an NFT from Pixel Punks" in response.content.decode()

    def test_liverefresh_integration_a_price_row_is_written_and_restored(self):
        """**A price row is a row of the log like any other, live and on reload.**"""
        price = {"kind": "price", "round": 41234572, "old": 0.214, "new": 0.2215, "pct": 3.5}
        block = _block(12, [price])
        self._latest(block)
        self._backlog(block, _block(11, [price]))
        user = _dynamic_reader("ll-price@example.com")
        user.profile.live_refresh = True
        user.profile.save()
        self.client.force_login(user)

        restored = self.client.get(reverse("swap_entry", args=[ADDRESS]))
        live = self._poll(user, since=11)

        assert "ALGO price 0.214 to 0.222 USD" in restored.content.decode()
        assert "ALGO price 0.214 to 0.222 USD" in live.content.decode()

    def test_liverefresh_integration_a_gap_longer_than_the_backlog_is_said(self):
        """**The backlog holds the last twenty, so a reader further behind has
        updates it can no longer be given. The log says how many.**"""
        latest = _block(8)
        self._latest(latest)
        self._backlog(latest, _block(7))
        user = _dynamic_reader("ll-gap@example.com")

        response = self._poll(user, since=1)

        assert "5 updates not received" in response.content.decode()

    def test_liverefresh_integration_the_classic_layout_gets_log_rows(self):
        """The classic layout has the log too, below the consolidated box."""
        block = _block(1, [FLOOR_MOVE])
        self._latest(block)
        self._backlog(block)
        user = _reader("ll-classic@example.com")
        user.profile.preferred_layout = "classic"
        user.profile.save()

        response = self._poll(user)

        assert "Floor of Pixel" in response.content.decode()


@override_settings(
    REDIS_DB=TEST_REDIS_DB,
    API_LIVE_ENABLED=True,
    API_LIVE_SHARED_TOKEN_USER_IDS=frozenset(),
)
class ApiLiveWarmSetTest(TestCase):
    """`lva` and `lvn`, the API's half of the same warm set.

    **Here rather than with the API tests, because it is the same contract.**
    `api/live.py` spends the *widget's* warm set - one budget per reader across
    both surfaces, from one table - and writes into the same `lvx` the widget
    writes. Testing it anywhere else would mean a second copy of this
    scaffolding and a second place for the key names to drift.

    **The asymmetry below is the thing to pin.** `lvx` members are address
    strings, because that is what the pass re-prices and what the widget
    writes; `lva` members are *page keys*, because that is what `_live_page`
    tests membership with once it has resolved the bundle. One function writes
    both, two lines apart, in the two different shapes - and until now a comment
    was the only thing saying so.
    """

    def setUp(self):
        """Note what is here, and remove only what a subscribe adds."""
        super().setUp()
        self.redis = _client()
        self.redis.zrem(SUBSCRIBED_KEY, ADDRESS)
        self.redis.zrem(API_WARM_KEY, ADDRESS)
        self.before = set(self.redis.scan_iter(count=1000))
        self.addCleanup(self._forget)

    def _forget(self):
        self.redis.zrem(SUBSCRIBED_KEY, ADDRESS)
        self.redis.zrem(API_WARM_KEY, ADDRESS)
        added = set(self.redis.scan_iter(count=1000)) - self.before
        if added:
            self.redis.delete(*added)

    def _subscribe(self, user, addresses=ADDRESS, value=ADDRESS):
        return subscribe(
            value,
            addresses,
            user.pk,
            user.profile.permission,
            client=self.redis,
        )

    def test_liverefresh_integration_a_subscription_reaches_both_keys(self):
        """One call, two keys, and the engine reads them for different
        questions: `lvx` is "re-price this", `lva` is "and publish a snapshot"."""
        user = _reader("lva-both@example.com", tier="Cluster")

        assert self._subscribe(user) is True
        assert ADDRESS in _engine_reads_subscriptions(self.redis, SUBSCRIBED_KEY)
        assert ADDRESS in _engine_reads_subscriptions(self.redis, API_WARM_KEY)

    def test_liverefresh_integration_the_two_keys_hold_different_shapes(self):
        """**Addresses in `lvx`, a page key in `lva`.**

        A bundle is where they part: the pass re-prices addresses, so `lvx`
        carries the space-joined list, while the snapshot is published under the
        bundle's hash and `lva` has to name that. Writing the same string into
        both would leave the engine either re-pricing nothing or publishing a
        snapshot nobody can find, depending which way round it was wrong.
        """
        user = _reader("lva-shapes@example.com", tier="Cluster")
        other = "7XBGHMVIQE6HC3RUFAB7NPPGWFQNJ4KMHGMLDLMBWAQHJ6GTSYPPQJGY3Q"
        addresses = f"{ADDRESS} {other}"
        bundle = page_key(ADDRESS, addresses)
        self.addCleanup(self.redis.zrem, SUBSCRIBED_KEY, addresses)
        self.addCleanup(self.redis.zrem, API_WARM_KEY, bundle)

        assert (
            subscribe(
                ADDRESS, addresses, user.pk, user.profile.permission, client=self.redis
            )
            is True
        )

        assert bundle != addresses, "a bundle key is not its address list"
        assert addresses in _engine_reads_subscriptions(self.redis, SUBSCRIBED_KEY)
        assert bundle in _engine_reads_subscriptions(self.redis, API_WARM_KEY)

    def test_liverefresh_integration_subscribing_is_off_by_default(self):
        """**It ships inert.** Subscribing is the first thing here that costs
        the *engine* something per block, and it starts the moment an entitled
        caller makes a request - there is no ramp."""
        user = _reader("lva-off@example.com", tier="Cluster")

        with override_settings(API_LIVE_ENABLED=False):
            assert self._subscribe(user) is False

        assert self.redis.zscore(API_WARM_KEY, ADDRESS) is None

    def test_liverefresh_integration_a_shared_token_never_subscribes(self):
        """**A per-account limit measures a person, and this is a population.**

        The mobile app ships one baked credential for its whole installed base,
        so subscribing would put every address any phone user glanced at into
        the live pass and spend one warm set of five between all of them.
        Checked after the tier because it is not a tier question - this account
        may be entitled twice over and still must not.
        """
        user = _reader("lva-shared@example.com", tier="Cluster")

        with override_settings(API_LIVE_SHARED_TOKEN_USER_IDS=frozenset({user.pk})):
            assert self._subscribe(user) is False

        assert self.redis.zscore(API_WARM_KEY, ADDRESS) is None

    def test_liverefresh_integration_a_tier_without_block_time_does_not(self):
        """The warm set is what block-time data costs, so a caller who is not
        served it must not be spending it."""
        user = _reader("lva-tier@example.com", tier="Intro")
        assert block_time(user.profile.permission) is False

        assert self._subscribe(user) is False
        assert self.redis.zscore(API_WARM_KEY, ADDRESS) is None

    def test_liverefresh_integration_a_published_snapshot_is_read_back(self):
        """`lvn:{page}`, msgpack, integer asset keys - the same
        `strict_map_key=False` the widget's payload read needs."""
        key = f"{SNAPSHOT_PREFIX}:{ADDRESS}"
        self.redis.set(
            key,
            msgpack.packb({"total": 42.0, "asaitems": [], "values": {31566704: 7.25}}),
            ex=120,
        )
        self.addCleanup(self.redis.delete, key)

        published = snapshot(ADDRESS, ADDRESS, client=self.redis)

        assert published["total"] == 42.0
        assert published["values"][31566704] == 7.25

    def test_liverefresh_integration_no_snapshot_means_the_cached_path(self):
        """**None is an answer, not a failure.**

        A page is not warm until a block has passed over it, so the first call
        of a new subscription is always the cached one. Raising here would turn
        an ordinary first request into an error.
        """
        assert snapshot(ADDRESS, ADDRESS, client=self.redis) is None
