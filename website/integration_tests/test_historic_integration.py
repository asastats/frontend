"""Integration tests for the Historic widget's engine seam.

**The last widget in the plan's list with no integration test**, and the only
one whose scopes `test_widget_scopes_integration.py` excuses for want of a home.
Five are declared and they are not equally callable:

* ``historic:events`` - a GET for a bundle's processing state.
* ``historic:timestamp`` - a POST that evaluates one point in a bundle's
  history.
* ``historic:evaluate`` - a POST that runs an evaluation for a period.
* ``historic:process`` - a POST that starts a real processing run.
* ``historic:reset`` - a DELETE that removes a reader's stored history.

**All five are now called, and the four that were deferred needed no seeded
reader after all.** The note that deferred them assumed a bundle with no
history could say nothing useful. Asked rather than assumed, three of them say
something the consumers depend on:

    historic:evaluate  POST  -> 200 {"type": "show_update"}
    historic:timestamp POST  -> 200 {"type": "show_update"}
    historic:reset     DELETE -> 204, empty
    historic:process   POST  -> 202, empty

``show_update`` is the exact branch both consumer methods take before they
reach ``data["extended_timestamps"]`` or ``data["data"]``. If the engine ever
stopped sending it for an unprocessed bundle, those methods would raise a
``KeyError`` *inside a websocket handler*, where there is nowhere for an error
to go but a silent disconnection - the reader watches a page that never
arrives. That is worth a test, and it costs a bundle nobody has processed.

**The engine these call is the suite's own**, started by
``integration_tests/conftest.py`` for the session and torn down after, against
its own database. So a ``DELETE`` here removes nothing anybody has, and the
``POST`` to ``process`` is accepted for a bundle hash that is not derived from
any address.

**The residual, and it was decided rather than left open.** ``process`` answers
202, which means it enqueues: every run of this suite puts one task on the
local engine's queue for a bundle hash derived from no address. Raised as a
reason to leave the test out, and **kept, 2026-09-24** - the 202 is a contract
the consumer depends on, the queue it touches is the suite's own, and a scope
called nowhere is a grant nobody notices the loss of.

What that task then does is the engine's business and is not asserted here.
Only that the endpoint accepts and returns promptly, which is what
``_initiate_update`` relies on when it tells the group the work is in progress
on the very next line.

**What the one read buys.** Two things that are otherwise asserted only against
mocks of the engine:

* the **grant** - `HasWidgetScope` answers 403 for a scope the deployment
  credential does not carry, and nothing else in this stack calls
  ``historic:events``, so a missing grant surfaces when a reader opens the page
* the **shape** - an unknown bundle answers an empty mapping rather than a
  404, which is what lets the consumer show an unprocessed page instead of
  disconnecting the reader.

**What this still does not cover, stated because the first draft pretended
otherwise.** `_restore_event_phase_keys` puts back the integer phase keys JSON
transport stringifies, and a bundle with no history answers ``{}`` - so the
engine's own phase payload never reaches it here. A test that looped over that
empty mapping would pass while asserting nothing.

What is covered instead is the mechanism itself, through the real transport
rather than a mock of it: a record shaped as the engine builds it, put through
``json.dumps``/``json.loads`` - which is precisely what the response did to it -
and asserted to come back with its integer keys. That is the conversion doing
its job against the thing that breaks it. Only "and the engine really sends
phases shaped like that" is left, and it needs a bundle whose history has been
processed.
"""

import json

from django.test import TestCase

from api.client import BackendError, engine_request
from widgets.inhouse.historic.consumers import _restore_event_phase_keys
from widgets.inhouse.historic.manifest import MANIFEST

#: A bundle hash nothing has ever processed.
#:
#: Forty hex characters, which is the shape the engine expects, and not derived
#: from a real address - the point is a bundle with no stored history, so the
#: read is safe to repeat and its answer is deterministic.
UNKNOWN_BUNDLE = "0123456789abcdef0123456789abcdef01234567"

#: Every scope this widget declares, pinned.
#:
#: Not a restatement of the manifest for its own sake: four of these are
#: deliberately not exercised anywhere, and the list above says why each one is
#: left out. A scope added without a decision would make that prose quietly
#: false, and this is what notices.
DECLARED_SCOPES = {
    "historic:evaluate",
    "historic:events",
    "historic:process",
    "historic:reset",
    "historic:timestamp",
}


class HistoricScopeTest(TestCase):
    """The declarations, which need no engine."""

    def test_integration_historic_declares_the_scopes_its_code_calls(self):
        """A manifest that drifts from the views fails in `engine_request`
        before a request is made, which is a 500 on the page rather than a
        refusal from the engine."""
        self.assertEqual(set(MANIFEST.engine_endpoints), DECLARED_SCOPES)

    def test_integration_historic_is_engine_backed(self):
        """`validate_manifest` forbids `public` with `engine_endpoints`, and
        this widget spends the deployment credential on five of them."""
        self.assertEqual(MANIFEST.capability, "engine-backed")

    def test_integration_a_scope_outside_the_manifest_is_refused_here(self):
        """The local half of the check: `engine_request` refuses before it
        sends, so a scope this widget never declared cannot spend the
        credential."""
        with self.assertRaises(BackendError):
            engine_request(
                "router:sweep",
                "GET",
                f"/api/v2/historic/{UNKNOWN_BUNDLE}/events/",
                MANIFEST.engine_endpoints,
            )


class HistoricEventsTest(TestCase):
    """The one scope that can be read without doing work for somebody."""

    def _events(self):
        """Ask the engine for a bundle nothing has processed."""
        return engine_request(
            "historic:events",
            "GET",
            f"/api/v2/historic/{UNKNOWN_BUNDLE}/events/",
            MANIFEST.engine_endpoints,
        )

    def test_integration_historic_events_is_granted(self):
        """**A 403 here is an ungranted scope, and it is invisible otherwise.**

        Nothing else in this stack calls `historic:events`, so the deployment
        credential's grant for it is proven by a reader opening the page or by
        nothing at all.
        """
        response = self._events()

        self.assertEqual(
            response.status_code,
            200,
            f"the engine answered {response.status_code} for historic:events; "
            "403 means the deployment credential does not carry the scope",
        )

    def test_integration_historic_events_answers_a_mapping(self):
        """The consumer indexes the result by bundle and by phase, so a list
        or a bare string would raise inside a websocket handler - where there
        is nowhere for the error to go but a silent disconnection."""
        payload = self._events().json()

        self.assertIsInstance(
            payload,
            dict,
            f"events came back as {type(payload).__name__}, not a mapping",
        )

    def test_integration_historic_events_is_empty_for_an_unknown_bundle(self):
        """**An empty mapping, not a 404**, which is the contract the consumer
        relies on.

        `_receive_events` does nothing when the payload is falsy and sends a
        processing update when it is not, so "this bundle has no history" has
        to arrive as something falsy rather than as an error. A 404 would reach
        the websocket handler as a `BackendError` and disconnect the reader
        instead of showing them an unprocessed page.
        """
        payload = self._events().json()

        self.assertEqual(payload, {})
        self.assertEqual(_restore_event_phase_keys(payload), {})


class HistoricUnprocessedBundleTest(TestCase):
    """The three scopes a bundle with no history can still answer for.

    **Deferred on an assumption that turned out to be wrong.** The note that
    deferred them said calling these would "assert nothing useful about a
    bundle with none". Asked instead of assumed, each one answers the contract
    its consumer is written against.
    """

    def _post(self, scope, path, body):
        return engine_request(
            scope,
            "POST",
            f"/api/v2/historic/{UNKNOWN_BUNDLE}/{path}/",
            MANIFEST.engine_endpoints,
            json=body,
        )

    def test_integration_historic_evaluate_asks_for_a_processing_run(self):
        """**The branch `_send_charts_data` takes before it indexes anything.**

        It reads `data["extended_timestamps"]` on the line after the
        `show_update` check. For a bundle with no history the check is what
        stops it, so an engine that answered anything else here would raise a
        `KeyError` inside a websocket handler - and a consumer that raises
        disconnects the reader rather than showing them a page.
        """
        response = self._post("historic:evaluate", "evaluate", {"period": None})

        self.assertEqual(
            response.status_code,
            200,
            f"the engine answered {response.status_code} for historic:evaluate; "
            "403 means the deployment credential does not carry the scope",
        )
        self.assertEqual(response.json(), {"type": "show_update"})

    def test_integration_historic_evaluate_says_the_same_for_a_real_period(self):
        """A period is what the reader's zoom sends, and an unprocessed bundle
        has to answer it the same way - otherwise the branch depends on which
        of the two call sites reached it."""
        response = self._post(
            "historic:evaluate", "evaluate", {"period": [1750000000, 1758000000]}
        )

        self.assertEqual(response.json(), {"type": "show_update"})

    def test_integration_historic_timestamp_asks_for_a_processing_run(self):
        """Same contract, same reason: `_send_assets_data` reads `data["data"]`
        on the line after its own `show_update` check."""
        response = self._post(
            "historic:timestamp", "timestamp", {"timestamp": 1758000000}
        )

        self.assertEqual(
            response.status_code,
            200,
            f"the engine answered {response.status_code} for historic:timestamp; "
            "403 means the deployment credential does not carry the scope",
        )
        self.assertEqual(response.json(), {"type": "show_update"})

    def test_integration_historic_reset_removes_nothing_and_says_so(self):
        """**A DELETE for a bundle with nothing stored is not an error.**

        `HistoricResetView` calls this and then redirects, with no branch for a
        failure - so an engine that answered 404 for "there was nothing to
        delete" would turn a reader pressing Reset on an unprocessed page into
        a `BackendError` and a 500.

        Safe to repeat: the engine under this suite is the one
        `integration_tests/conftest.py` starts, against its own database, and
        this bundle hash is not derived from any address.
        """
        response = engine_request(
            "historic:reset",
            "DELETE",
            f"/api/v2/historic/{UNKNOWN_BUNDLE}/",
            MANIFEST.engine_endpoints,
        )

        self.assertEqual(
            response.status_code,
            204,
            f"the engine answered {response.status_code} for historic:reset; "
            "403 means the deployment credential does not carry the scope",
        )

    def test_integration_historic_process_is_accepted_rather_than_done(self):
        """**202, and the number is the contract.**

        `_initiate_update` sends a "processing" message to the group on the
        line after this call, which is only honest if the call returned before
        the work did. A 200 carrying a finished result would mean the reader is
        shown "processing" for something already over; a synchronous run would
        hold the websocket open for as long as it took.

        What the enqueued task then does for a bundle hash derived from no
        address is the engine's business and is not asserted here. That this
        test enqueues anything at all was raised as a reason to leave it out
        and decided against on 2026-09-24: the queue is the suite's own, and a
        scope called nowhere is a grant whose loss nothing would notice.
        """
        response = self._post(
            "historic:process",
            "process",
            {"bundle": UNKNOWN_BUNDLE, "period": None},
        )

        self.assertEqual(
            response.status_code,
            202,
            f"the engine answered {response.status_code} for historic:process; "
            "403 means the deployment credential does not carry the scope",
        )


class HistoricPhaseKeysTest(TestCase):
    """The conversion the events read cannot exercise.

    A bundle with no history answers `{}`, so the engine's own phase payload
    never reaches `_restore_event_phase_keys` in this suite. What can be
    exercised is the thing that breaks it - JSON transport - against a record
    shaped the way the engine builds one.
    """

    #: One address record as the engine assembles it, with integer phase keys.
    RECORD = {
        "bundle": "0123456789abcdef0123456789abcdef01234567",
        "addresses": ["AAAA", "BBBB"],
        "AAAA": {1: ["queued"], 2: ["running", 4], 3: []},
    }

    def test_integration_historic_phase_keys_survive_the_json_round_trip(self):
        """**The whole reason this function exists**, against the real
        transport rather than a mock of it.

        `json.dumps` turns an integer key into a string and `json.loads` leaves
        it one, so the engine's `{1: …}` arrives as `{"1": …}`. `UpdateStatus`
        and the finished-state check index by integer, so without the
        conversion every phase lookup misses and a processing page reports
        nothing happening while everything happens.
        """
        transported = json.loads(json.dumps(self.RECORD))

        # The damage, asserted first: without this the test below could pass
        # against a payload that never lost anything.
        self.assertEqual(set(transported["AAAA"]), {"1", "2", "3"})

        restored = _restore_event_phase_keys(transported)

        self.assertEqual(set(restored["AAAA"]), {1, 2, 3})
        self.assertEqual(restored["AAAA"][2], ["running", 4])

    def test_integration_historic_phase_keys_leave_the_non_mappings_alone(self):
        """`bundle` is a string and `addresses` a list, and neither has phases.
        Converting them would raise rather than mangle, which is why the
        function tests each value rather than assuming the shape."""
        restored = _restore_event_phase_keys(json.loads(json.dumps(self.RECORD)))

        self.assertEqual(restored["bundle"], self.RECORD["bundle"])
        self.assertEqual(restored["addresses"], ["AAAA", "BBBB"])
