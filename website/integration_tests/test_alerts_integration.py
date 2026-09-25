"""Integration tests for the Alerts widget against a real Redis.

**Why this suite exists at all, when the widget holds no engine privilege.**
Every other integration test here points at the engine on :8001; alerts has
``capability = "public"`` and no ``engine_endpoints``, so there is nothing to
point at. Its seam is somewhere else, and it is a worse one: **Redis, shared
with a different repository**. The engine writes six keys that this widget
reads, and the unit suite asserts every one of those formats against a
``MagicMock`` that agrees with whatever it is told.

So what is tested below is the half nothing else can see - that the bytes one
repository writes are the bytes the other repository reads.

**The engine's writes are reproduced here literally**, from
``engine/utils/cache.py``, because there is no shared code to import and a
paraphrase would defeat the point::

    pipeline.zadd(key, {f"{bucket}:{float(total)!r}": bucket})

That is a weakness worth naming: if the engine changes its format, this suite
goes on asserting the old one. What it does catch is the *website* drifting,
which is the direction that has actually happened - and a change on either side
now has a place that spells the contract out.

**On the database.** These tests write to Redis db 15 rather than the shared
db 0. ``publish_assets`` deletes and rewrites a whole key from the database's
contents, so running it against the real set would wipe what the engine is
using. The keys written are removed afterwards rather than the database being
flushed: an empty db is not a reason to treat it as disposable.

**On what is not here.** Nothing subscribes to a real push service - that needs
a browser and a permission prompt. What *is* tested is that a real VAPID key
pair produces a request ``pywebpush`` will build, which is the part that broke
once already: the ``sub`` claim must be a ``mailto:`` URI, and the runbook still
asks for that to be checked by hand.
"""

import hashlib
import hmac
import json
import time
import uuid

import msgpack
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from redis import Redis

from widgets.inhouse.alerts.evaluate import (
    ASSET_HISTORY_KEY,
    HISTORY_KEY,
    payload_for,
    percent_move,
)
from widgets.inhouse.alerts.models import AlertRule, Direction, PushSubscription, Subject
from widgets.inhouse.alerts.population import (
    RULE_ASSETS_KEY,
    RULES_KEY,
    publish_assets,
    publish_page,
    published_assets,
    published_pages,
)
from widgets.inhouse.alerts.views import SIGNATURE_HEADER

#: The database these tests own. See the module docstring.
TEST_REDIS_DB = 15

#: The engine's tick and retention, from `utils/constants/cache.py`.
#:
#: Named here rather than imported because they are the *other* repository's
#: constants: this suite exists to state the contract, and importing it from
#: one side would mean only one side has to keep it.
TICK_SECONDS = 300
RETENTION_SECONDS = 604800

#: A shared secret for the two receiving endpoints. Any value does - what is
#: being tested is that the same bytes are signed and checked on both sides.
WEBHOOK_SECRET = "integration-secret"


def _client():
    """Return a client on the database these tests own."""
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT_LOCAL,
        db=TEST_REDIS_DB,
        password=settings.REDIS_AUTH,
    )


def _engine_writes_history(client, key, value, at):
    """Write one history point exactly as the engine's pipeline does.

    Copied from ``engine/utils/cache.py``'s ``mupdate_live_total_history`` and
    ``mupdate_live_asset_history``, which are identical in shape. The member is
    ``{bucket}:{repr(float(value))}`` scored by the bucket - the timestamp has
    to be the score because a sorted set has only one number per member, so the
    value rides in the member and is parsed back out.

    :param client: an open Redis client
    :param key: the full key, `lvth:{page}` or `lvah:{asset id}`
    :type key: str
    :param value: the total or price at that moment
    :param at: unix time of the reading
    :type at: float
    """
    bucket = int(at // TICK_SECONDS) * TICK_SECONDS
    pipeline = client.pipeline()
    pipeline.zremrangebyscore(key, bucket, bucket)
    pipeline.zadd(key, {f"{bucket}:{float(value)!r}": bucket})
    pipeline.zremrangebyscore(key, "-inf", bucket - RETENTION_SECONDS)
    pipeline.expire(key, RETENTION_SECONDS)
    pipeline.execute()


@override_settings(REDIS_DB=TEST_REDIS_DB)
class AlertsRedisContractTest(TestCase):
    """The formats the two repositories agree about, against a real server."""

    def setUp(self):
        """Give each test its own page and asset, and forget them afterwards."""
        super().setUp()
        self.redis = _client()
        # Unique per test, so a crashed run cannot make the next one pass or
        # fail for the wrong reason.
        self.page = f"ITEST{uuid.uuid4().hex.upper()}"[:40]
        self.asset_id = 999_000_000_000 + int(uuid.uuid4().int % 1_000_000)
        self.keys = [
            f"{HISTORY_KEY}:{self.page}",
            f"{ASSET_HISTORY_KEY}:{self.asset_id}",
            f"lvp:{self.page}",
        ]
        self.addCleanup(self._forget)

    def _forget(self):
        """Delete only what this test wrote.

        Never `flushdb`: the database being empty when this was written is not a
        reason to treat whatever is in it next year as disposable.
        """
        self.redis.delete(*self.keys)
        self.redis.zrem(RULES_KEY, self.page)
        self.redis.zrem(RULE_ASSETS_KEY, str(self.asset_id))

    def test_alerts_integration_a_totals_move_is_read_back(self):
        """**The highest-value assertion in this file.**

        The engine writes `lvth:{page}`; `percent_move` parses it. Two
        repositories, no shared code, and until now no test that saw both ends.
        """
        now = time.time()
        _engine_writes_history(
            self.redis, f"{HISTORY_KEY}:{self.page}", 100.0, now - 7200
        )

        move = percent_move(self.page, 3600, 110.0, client=self.redis, now=now)

        assert move == pytest.approx(10.0)

    def test_alerts_integration_an_asset_move_is_read_back(self):
        """The same read on the per-asset series, which is the same shape by
        design - one `percent_move` answers both, differing only in the key."""
        now = time.time()
        _engine_writes_history(
            self.redis, f"{ASSET_HISTORY_KEY}:{self.asset_id}", 0.5, now - 7200
        )

        move = percent_move(
            self.asset_id,
            3600,
            0.55,
            client=self.redis,
            now=now,
            prefix=ASSET_HISTORY_KEY,
        )

        assert move == pytest.approx(10.0)

    def test_alerts_integration_a_small_price_survives_the_round_trip(self):
        """**`repr(float(x))` is the format, and it is not `str` of a Decimal.**

        An ASA priced at 1.23e-08 is ordinary. If the member were written with
        `str()` of a `Decimal` or with a fixed precision, this is where it would
        come back as zero and every percentage rule on a small asset would read
        a move of -100%.
        """
        now = time.time()
        _engine_writes_history(
            self.redis, f"{ASSET_HISTORY_KEY}:{self.asset_id}", 1.23e-08, now - 7200
        )

        move = percent_move(
            self.asset_id,
            3600,
            1.353e-08,
            client=self.redis,
            now=now,
            prefix=ASSET_HISTORY_KEY,
        )

        assert move == pytest.approx(10.0, rel=1e-3)

    def test_alerts_integration_a_history_too_short_answers_nothing(self):
        """**The rule that makes the window mean what it says.**

        One point, written now, cannot answer "how far has it moved in an
        hour". Answering from it would turn "down 5% in 24 hours" into "down 5%
        since we started watching", and the notification would look identical.
        """
        now = time.time()
        _engine_writes_history(self.redis, f"{HISTORY_KEY}:{self.page}", 100.0, now)

        assert percent_move(self.page, 3600, 110.0, client=self.redis, now=now) is None

    def test_alerts_integration_the_far_edge_is_at_or_before_the_window(self):
        """A point *inside* the window must not answer for the window's edge.

        Two points, one 30 minutes old and one two hours old: an hour's window
        has to compare against the older one.
        """
        now = time.time()
        key = f"{HISTORY_KEY}:{self.page}"
        _engine_writes_history(self.redis, key, 100.0, now - 7200)
        _engine_writes_history(self.redis, key, 200.0, now - 1800)

        move = percent_move(self.page, 3600, 110.0, client=self.redis, now=now)

        assert move == pytest.approx(10.0), "it compared against the newer point"

    def test_alerts_integration_the_engine_keeps_one_point_per_tick(self):
        """Two writes landing in one five-minute bucket leave one member.

        Without the `zremrangebyscore` before the `zadd` the set keeps both, and
        which one answers depends on the order Redis returns them - a
        percentage that alternates between two values for no visible reason.
        """
        now = time.time()
        key = f"{HISTORY_KEY}:{self.page}"
        _engine_writes_history(self.redis, key, 100.0, now)
        _engine_writes_history(self.redis, key, 101.0, now + 5)

        assert self.redis.zcard(key) == 1

    def test_alerts_integration_the_series_is_given_a_lifetime(self):
        """A page whose rules are all deleted stops being written to, and the
        key would otherwise sit in Redis for as long as the server runs."""
        key = f"{HISTORY_KEY}:{self.page}"
        _engine_writes_history(self.redis, key, 100.0, time.time())

        assert 0 < self.redis.ttl(key) <= RETENTION_SECONDS

    def test_alerts_integration_the_published_payload_is_read_back(self):
        """**`strict_map_key=False`, and integer asset keys.**

        The live pass publishes msgpack with the asset id as an *integer* key.
        Unpacking without that flag raises; unpacking into string keys would
        make `reading_for` miss every `asa_total` rule and report "no reading"
        for all of them - which is silence, not an error.
        """
        packed = msgpack.packb(
            {"total": 1234.5, "priceusdc": 0.25, "values": {31566704: 7.25}}
        )
        self.redis.set(f"lvp:{self.page}", packed)

        payload = payload_for(self.page, client=self.redis)

        assert payload["total"] == 1234.5
        assert payload["values"][31566704] == 7.25

    def test_alerts_integration_a_page_never_published_is_none(self):
        """Not an empty dict: the modal shows no reference figure rather than a
        zero, which would read as "your portfolio is worth nothing"."""
        assert payload_for(self.page, client=self.redis) is None

    def test_alerts_integration_the_rule_population_round_trips(self):
        """`lvr` is what makes the engine re-price a page nobody is looking at.

        Written by this widget, read by the engine's live pass. The assertion
        that matters is that `zadd` and `zrange` agree about member encoding -
        the engine reads this set whole, and a page it cannot decode is a page
        whose alerts never fire.
        """
        user = _reader("population@example.com")
        AlertRule.objects.create(
            user=user,
            subject=Subject.TOTAL_VALUE,
            direction=Direction.DOWN,
            threshold="100",
            address=self.page,
        )

        assert publish_page(self.page, client=self.redis) is True
        assert self.page in published_pages(client=self.redis)

    def test_alerts_integration_a_page_leaves_when_its_last_rule_does(self):
        """Recomputed rather than decremented: a page wrongly left behind is
        re-priced for nobody, which is invisible and not free."""
        publish_page(self.page, client=self.redis)

        assert publish_page(self.page, client=self.redis) is False
        assert self.page not in published_pages(client=self.redis)

    def test_alerts_integration_a_priced_asset_reaches_the_task(self):
        """`lvra` is the only thing that puts an asset in front of the periodic
        price task, and `published_assets` decodes it back to integers - the
        engine's `cached_live_rule_assets` does the same on its side."""
        user = _reader("assets@example.com")
        AlertRule.objects.create(
            user=user,
            subject=Subject.ASA_PRICE_PERCENT,
            direction=Direction.DOWN,
            threshold="5",
            asset_id=self.asset_id,
            window_seconds=3600,
        )

        assert publish_assets(client=self.redis) == 1
        assert published_assets(client=self.redis) == (self.asset_id,)


def _reader(email, permission=None):
    """Return a user at a tier that admits rules."""
    from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS  # noqa: PLC0415

    user = get_user_model().objects.create_user(username=email, email=email, password="x")
    profile = user.profile
    profile.permission = (
        SUBSCRIPTION_TIER_PERMISSIONS["Professional"]
        if permission is None
        else permission
    )
    profile.save()
    return user


@override_settings(REDIS_DB=TEST_REDIS_DB, ALERTS_WEBHOOK_SECRET=WEBHOOK_SECRET)
class AlertsWebhookEndToEndTest(TestCase):
    """The engine's two calls, signed and received for real.

    **Three halves that are only ever tested against mocks of each other**: the
    signature, the URL, and the evaluation. Here they run together over the real
    request path, with a real payload in Redis, so a route that moved or a
    signature computed over the wrong bytes fails here rather than in
    production at the moment a rule should have fired.
    """

    def setUp(self):
        """A reader with a browser, a rule, and a page the pass has published."""
        super().setUp()
        self.redis = _client()
        self.page = f"ITEST{uuid.uuid4().hex.upper()}"[:40]
        self.asset_id = 999_000_000_000 + int(uuid.uuid4().int % 1_000_000)
        self.addCleanup(self.redis.delete, f"lvp:{self.page}")

        self.user = _reader("webhook@example.com")
        PushSubscription.objects.create(
            user=self.user,
            endpoint="https://push.example/webhook",
            p256dh="p",
            auth="a",
        )
        self.client = Client()

    def _post(self, url_name, body):
        """Send `body` signed the way the engine signs it.

        Over the exact bytes, which is the point: a signature over a
        re-serialized dict would pass here and fail against the engine.
        """
        raw = json.dumps(body).encode()
        digest = hmac.new(WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
        # `SIGNATURE_HEADER` is already the `request.META` key the view reads,
        # not the wire name - so it is passed through as-is rather than
        # mangled into one.
        return self.client.post(
            reverse(url_name),
            data=raw,
            content_type="application/json",
            **{SIGNATURE_HEADER: f"sha256={digest}"},
        )

    def _rule(self, **overrides):
        fields = {
            "user": self.user,
            "subject": Subject.TOTAL_VALUE,
            "direction": Direction.DOWN,
            "threshold": "100",
            "address": self.page,
            "last_value": "120",
        }
        fields.update(overrides)
        return AlertRule.objects.create(**fields)

    def test_alerts_integration_a_repriced_page_fires_a_rule(self):
        """The live pass says "page X moved"; everything else is read here."""
        self._rule()
        self.redis.set(f"lvp:{self.page}", msgpack.packb({"total": 90.0, "values": {}}))

        response = self._post("alerts_repriced", {"page": self.page})

        assert response.status_code == 200
        assert response.json()["fired"] == 1

    def test_alerts_integration_a_priced_asset_fires_a_rule(self):
        """**The one call that carries a number rather than a page name.**

        An asset's price is not in the shared Redis - it lives in the engine's
        own cache - so it arrives in the signed body, and the signature is what
        makes that number trustworthy.
        """
        self._rule(
            subject=Subject.ASA_PRICE,
            asset_id=self.asset_id,
            address="",
            threshold="1",
            last_value="2",
        )

        response = self._post("alerts_priced", {"prices": {str(self.asset_id): 0.5}})

        assert response.status_code == 200
        assert response.json()["fired"] == 1

    def test_alerts_integration_a_wrong_signature_is_refused(self):
        """Refused rather than ignored: anything that can reach this endpoint
        can otherwise assert any price it likes about any asset."""
        self._rule()
        raw = json.dumps({"page": self.page}).encode()

        response = self.client.post(
            reverse("alerts_repriced"),
            data=raw,
            content_type="application/json",
            HTTP_X_ASASTATS_ALERTS_SIGNATURE="sha256=" + "0" * 64,
        )

        assert response.status_code == 403

    def test_alerts_integration_the_url_the_engine_is_configured_with(self):
        """**A 301 here cost a live afternoon.** `requests` follows a redirect
        by turning the POST into a GET, so a trailing-slash mismatch reaches a
        POST-only view as a GET and answers 405 - which reads as the endpoint
        being wrong rather than the URL.
        """
        assert reverse("alerts_repriced") == "/widgets/alerts/repriced"
        assert reverse("alerts_priced") == "/widgets/alerts/priced"


class AlertsPushRequestTest(TestCase):
    """A real VAPID pair, and the claim shape that broke once.

    Nothing is delivered: there is no push service here and a browser
    subscription cannot be minted without one. What is asserted is that a real
    key pair produces a request `pywebpush` accepts - which is the half the
    runbook still asks to be checked by hand.
    """

    def test_alerts_integration_a_real_vapid_pair_signs_a_request(self):
        """**The `sub` claim must be a `mailto:` URI, and it must survive.**

        Asserted by decoding the token rather than by looking at the header's
        scheme: which scheme `py_vapid` emits is the library's business and has
        changed between drafts, while what the push service reads is the claim
        inside. A bare address is accepted by our own configuration and
        rejected there, so it fails at the only moment it matters - when
        somebody is waiting for a notification.
        """
        import base64  # noqa: PLC0415

        from py_vapid import Vapid01  # noqa: PLC0415

        vapid = Vapid01()
        vapid.generate_keys()
        claims = {"sub": "mailto:alerts@example.com", "aud": "https://push.example"}

        headers = vapid.sign(claims)

        token = headers["Authorization"].split()[-1].split(",")[0]
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))

        assert decoded["sub"] == "mailto:alerts@example.com"
        assert decoded["aud"] == "https://push.example"
        assert decoded["exp"] > time.time()

    def test_alerts_integration_a_bare_address_is_not_a_sub_claim(self):
        """The failure this pins is silent in every other suite: our own
        settings accept the string, and only the service complains."""
        from py_vapid import Vapid01, VapidException  # noqa: PLC0415

        vapid = Vapid01()
        vapid.generate_keys()

        with pytest.raises((VapidException, ValueError)):
            vapid.sign({"sub": "alerts@example.com", "aud": "https://push.example"})


class AlertsMigrationsTest(TestCase):
    """The widget's tables, which is the first thing a deploy gets wrong.

    Alerts is the first widget to keep a table at all, and `widgets/models.py`
    has to name the module or Django never imports it - a widget that adds a
    model without that line gets no table and no error until something reads it.
    """

    def test_alerts_integration_the_rule_table_exists(self):
        assert AlertRule.objects.count() == 0

    def test_alerts_integration_the_subscription_table_exists(self):
        assert PushSubscription.objects.count() == 0

    def test_alerts_integration_the_subject_column_fits_every_subject(self):
        """**Migration `0003`, and the reason for it.**

        `subject` was 16 characters, which fitted the first four names and not
        `asa_price_percent` at 17. Without the widening a reader saving one gets
        `value too long for type character varying(16)` - from the database, at
        the moment they press Add.
        """
        user = _reader("migrations@example.com")

        for subject, _ in Subject.choices:
            rule = AlertRule.objects.create(
                user=user,
                subject=subject,
                direction=Direction.DOWN,
                threshold="1",
                asset_id=1,
                address="A" * 40,
                window_seconds=3600,
            )
            rule.refresh_from_db()
            assert rule.subject == subject
