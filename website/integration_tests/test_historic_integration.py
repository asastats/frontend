"""Integration tests for the Historic widget's engine seam.

**The last widget in the plan's list with no integration test**, and the only
one whose scopes `test_widget_scopes_integration.py` excuses for want of a home.
Five are declared and they are not equally callable:

* ``historic:events`` - a GET for a bundle's processing state. **A read, and
  safe for a bundle nothing has ever processed**, which is what is tested here.
* ``historic:timestamp`` - a POST that evaluates one point in a bundle's
  history.
* ``historic:evaluate`` - a POST that runs an evaluation for a period.
* ``historic:process`` - a POST that starts a real processing run.
* ``historic:reset`` - a DELETE that removes a reader's stored history.

The last four are left to a suite with its own seeded reader and its own
cleanup. Calling them from here would either do real work on somebody's data or
assert nothing useful about a bundle with none, and a test that starts a
processing run as a side effect is one nobody will want to run twice.

**What the one read buys.** Two things that are otherwise asserted only against
mocks of the engine:

* the **grant** - `HasWidgetScope` answers 403 for a scope the deployment
  credential does not carry, and nothing else in this stack calls
  ``historic:events``, so a missing grant surfaces when a reader opens the page
* the **shape** - an unknown bundle answers an empty mapping rather than a
  404, which is what lets the consumer show an unprocessed page instead of
  disconnecting the reader.

**What this does not cover, stated because the first draft pretended
otherwise.** `_restore_event_phase_keys` puts back the integer phase keys JSON
transport stringifies, and a bundle with no history answers ``{}`` - so the
conversion itself still runs only against mocks. A test that looped over that
empty mapping would pass while asserting nothing, which is worse than the gap
it papers over. Covering it needs a bundle whose history has really been
processed, and that belongs with the seeded-reader suite the four unexercised
scopes are waiting for.
"""

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
