"""The engine really calling this website's alerts endpoint.

**The contract nobody checks.** Both halves of this webhook are unit-tested
against mocks of each other: the engine's `notify_repriced` posts to a
`MagicMock` session, and the website's `AlertsRepricedView` reads a request a
test built. Neither has ever met the other, so every assumption they share -
the signature's header name, what exactly is hashed, the JSON separators, the
trailing slash - is agreed between two fictions.

That is not hypothetical. The two things that have actually gone wrong with this
endpoint were both of that shape: a URL naming the bare domain, so nginx's 301
turned the POST into a GET and the view answered 405; and a signature computed
over a re-serialised body rather than the bytes sent.

**Why a subprocess rather than an import.** Both projects have a top-level
``utils`` package. Importing the engine's ``utils.alerts`` into this process
would either collide with the website's own or silently resolve to it, and a
test that imported the wrong module while claiming to test the other is worse
than no test. So the engine runs where it lives, in its own interpreter, with
its own settings - which is also the only arrangement that deserves the name
"cross-process".

**What it proves that nothing else does.** The bytes one project signs are the
bytes the other verifies, over a real socket, and the rule on the far side
actually fires.
"""

import json
import os
import subprocess
import uuid

import msgpack
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import LiveServerTestCase, override_settings
from redis import Redis

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from widgets.inhouse.alerts.models import AlertRule, Direction, PushSubscription, Subject

#: The database these tests own, as the other alerts integration files use.
TEST_REDIS_DB = 15

#: A secret both sides are given, for this run only.
WEBHOOK_SECRET = "cross-process-secret"

#: The engine, where the rest of this suite already runs it from.
BACKEND_PYTHON = os.path.expanduser("~/dev/venvs/backend/bin/python")
BACKEND_DIR = os.path.expanduser("~/dev/backend/engine/")

#: What the subprocess runs.
#:
#: Deliberately tiny: it imports the engine's own notifier and calls it. Every
#: byte on the wire is the engine's, including the ones this test would
#: otherwise have had to guess.
ENGINE_SCRIPT = """
import json, sys
from utils.alerts import notify_repriced, notify_priced

which = sys.argv[1]
if which == "repriced":
    print(json.dumps({"accepted": bool(notify_repriced(sys.argv[2]))}))
else:
    print(json.dumps({"accepted": bool(notify_priced({int(sys.argv[2]): 0.5}))}))
"""


def _engine_available():
    """Whether the engine checkout and its interpreter are both here.

    :return: Boolean
    """
    return os.path.exists(BACKEND_PYTHON) and os.path.exists(BACKEND_DIR)


@override_settings(REDIS_DB=TEST_REDIS_DB, ALERTS_WEBHOOK_SECRET=WEBHOOK_SECRET)
class AlertsWebhookCrossProcessTest(LiveServerTestCase):
    """The engine's notifier against this site, over a socket."""

    def setUp(self):
        """A reader with a browser, a rule, and a page the pass has published."""
        super().setUp()
        if not _engine_available():
            self.skipTest(f"no engine checkout at {BACKEND_DIR}")

        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT_LOCAL,
            db=TEST_REDIS_DB,
            password=settings.REDIS_AUTH,
        )
        self.page = f"XPROC{uuid.uuid4().hex.upper()}"[:40]
        self.asset_id = 999_000_000_000 + int(uuid.uuid4().int % 1_000_000)
        self.addCleanup(self.redis.delete, f"lvp:{self.page}")

        user = get_user_model().objects.create_user(
            username="xproc@example.com", email="xproc@example.com", password="x"
        )
        profile = user.profile
        profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Professional"]
        profile.save()
        PushSubscription.objects.create(
            user=user, endpoint="https://push.example/x", p256dh="p", auth="a"
        )
        self.user = user

    def _run_engine(self, which, argument):
        """Call the engine's notifier in its own interpreter.

        The engine reads its own `.env` from its own directory, and
        `load_dotenv` does not override variables already in the environment -
        so what is passed here wins, and nothing else of the engine's
        configuration is disturbed.

        **Only the repriced URL is configured, for either call.** The engine
        derives the prices endpoint by swapping a trailing `repriced` for
        `priced`, deliberately - one setting rather than two, because the second
        would only ever differ in its last path segment and would be a second
        thing to get right in a hand-edited `.env`. Telling it the priced URL
        directly would bypass the derivation and test nothing: the first draft
        of this did, and the engine cheerfully posted to
        `/widgets/alerts/priced/priced`.

        :param which: "repriced" or "priced"
        :type which: str
        :param argument: the page, or the asset id
        :return: what the engine printed, decoded
        :rtype: dict
        """
        environment = {
            "PATH": os.environ["PATH"],
            "HOME": os.environ["HOME"],
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "DJANGO_SETTINGS_MODULE": "engine.settings",
            # **The live server's own address.** `LiveServerTestCase` binds a
            # real port and serves the test database, so the engine posts at
            # this process and the rule it fires is the one created above.
            "ALERTS_WEBHOOK_URL": (
                f"{self.live_server_url}/widgets/alerts/repriced"
            ),
            "ALERTS_WEBHOOK_SECRET": WEBHOOK_SECRET,
        }
        completed = subprocess.run(
            [BACKEND_PYTHON, "-c", ENGINE_SCRIPT, which, str(argument)],
            cwd=BACKEND_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if completed.returncode != 0:
            self.fail(
                "the engine's notifier did not run:\n"
                f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
            )
        # The notifier logs warnings to stderr; the last stdout line is ours.
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        self.assertTrue(lines, f"engine printed nothing; stderr: {completed.stderr}")
        return json.loads(lines[-1])

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

    def test_integration_the_engine_signature_is_accepted_here(self):
        """**One socket, two projects, and no mock of either.**

        The engine builds the body, hashes it with its own secret and names its
        own header; this site hashes what arrived and compares. Everything they
        must agree about is exercised at once, and nothing in this test states
        what any of it is.
        """
        self._rule()
        self.redis.set(
            f"lvp:{self.page}", msgpack.packb({"total": 90.0, "values": {}})
        )

        answer = self._run_engine("repriced", self.page)

        self.assertTrue(
            answer["accepted"],
            "the website refused the engine's own signature",
        )

    def test_integration_the_rule_on_this_side_really_fires(self):
        """The whole path: engine process, socket, signature, evaluation, row.

        Asserted on the database rather than on the response, because what the
        reader gets out of this is a notification - and `last_fired_at` moving
        is the only durable evidence that the far side did the work.
        """
        rule = self._rule()
        self.redis.set(
            f"lvp:{self.page}", msgpack.packb({"total": 90.0, "values": {}})
        )

        self._run_engine("repriced", self.page)

        rule.refresh_from_db()
        self.assertIsNotNone(
            rule.last_fired_at, "the crossing never reached the far side"
        )

    def test_integration_the_priced_call_carries_its_body(self):
        """The other endpoint, whose body is an answer rather than a trigger.

        An asset's price is not in the shared Redis, so it travels in the
        signed body - which makes this the call where the signature is doing
        the most work.

        **And the URL is derived, not configured.** The engine swaps a trailing
        `repriced` for `priced`; nothing but a real request proves that lands on
        a route this site serves. It did not, the first time this test was
        written - `/widgets/alerts/priced/priced`, because the test had
        configured the endpoint it meant to derive.
        """
        rule = self._rule(
            subject=Subject.ASA_PRICE,
            asset_id=self.asset_id,
            address="",
            threshold="1",
            last_value="2",
        )

        answer = self._run_engine("priced", self.asset_id)

        self.assertTrue(answer["accepted"])
        rule.refresh_from_db()
        self.assertIsNotNone(rule.last_fired_at)

    def test_integration_a_different_secret_is_refused(self):
        """**The refusal has to work across the socket too.**

        A check that only ever passes is a check nobody has tested. This is the
        same call with the engine holding a secret the website does not.
        """
        self._rule()
        self.redis.set(
            f"lvp:{self.page}", msgpack.packb({"total": 90.0, "values": {}})
        )

        with override_settings(ALERTS_WEBHOOK_SECRET="something-else"):
            answer = self._run_engine("repriced", self.page)

        self.assertFalse(
            answer["accepted"], "a body signed with the wrong secret was accepted"
        )
