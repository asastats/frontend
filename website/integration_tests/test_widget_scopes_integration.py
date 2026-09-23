"""Integration tests for every engine-backed widget's own scope grant.

**The question the plan asked, and the answer.** `test_swap_integration.py`
exercises `account:holdings` and `assets:lookup` - but through *swapcore's*
manifest, and only that one. `haystack`, `folks` and `hogswap` declare exactly
the same two scopes and were never called through their own manifests, and
`asastats` has its own file that does not cover these two either.

That gap is narrow but it is real, because a scope is checked twice and the two
checks fail differently:

* **In this process.** `api.client.engine_request` refuses any scope the
  calling widget did not declare, raising `BackendError` before a request is
  made. A widget whose manifest drifts from what its views call fails here.
* **On the engine.** `HasWidgetScope` refuses any scope the *deployment
  credential* does not carry, answering **403**. A widget that declares a scope
  nobody granted fails here - and only at the moment a reader presses the
  button, because nothing else in this stack ever calls it.

So the test is per widget rather than per scope: the same call, made the way
each widget makes it.

**The guard at the bottom is the part that keeps this honest.** Listing four
widgets and two scopes in a file is how a fifth widget gets added and quietly
goes untested. `test_every_engine_backed_scope_is_accounted_for` fails when any
manifest declares a scope this file neither exercises nor has deliberately
excused, so a new scope forces a decision instead of a silence.

**On what is deliberately not called.** `router:quote` builds a real quote
against the chain and `router:group` a real transaction group. They are excused
by name below with the reason, not skipped by omission - the difference being
that an excuse is visible in a diff.

**Three excuses came off on 2026-09-24**, which is what the list is for. The
five `historic:*` scopes were excused as needing "a reader's stored history";
asked instead of assumed, four of them answer a bundle with *no* history with
the contract their consumer is written against, so they are covered in
`test_historic_integration.py` and named here as such rather than deleted.
"""

import importlib

from django.test import TestCase

from api.client import BackendError, fetch_account_holdings, fetch_asset_matches

#: An address the engine really knows, as the swap suite uses.
LINKED_ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

#: A query `assets:lookup` answers with something.
KNOWN_QUERY = "USDC"

#: Every in-house widget, by module name.
WIDGETS = (
    "alerts",
    "asastats",
    "dustsweep",
    "folks",
    "haystack",
    "historic",
    "hogswap",
    "liverefresh",
    "swapcore",
)

#: The scopes this file really calls, one test each.
#:
#: Both are GETs that change nothing, which is why they can be called for every
#: widget that declares them rather than once for the family. A set rather than
#: a table of callables: the two tests below name their own call, and a mapping
#: whose values nothing invokes reads like a dispatcher that is not one.
EXERCISED = frozenset({"account:holdings", "assets:lookup"})

#: The widgets that must be reached by the two calls above.
#:
#: **Named, so the loops cannot go quiet.** Both tests collect refusals into a
#: dict and assert it is empty, which is exactly the shape that passes when the
#: loop ran over nothing - a broken discovery, a renamed manifest attribute, a
#: filter that excludes everything. Adding a widget means adding it here
#: deliberately, the same way a new scope has to be exercised or excused.
EXPECTED_READERS = {
    "asastats",
    "dustsweep",
    "folks",
    "haystack",
    "hogswap",
    "swapcore",
}

#: Scopes deliberately not called here, and why each one is left out.
#:
#: **Named rather than omitted.** An excuse in a dict is visible when somebody
#: changes it; a scope simply missing from the table above is invisible for
#: ever. Each of these wants its own test with its own setup, not a line here.
EXCUSED = {
    "historic:process": "covered by `test_historic_integration.py`, grant included",
    "historic:reset": "covered by `test_historic_integration.py`, grant included",
    "historic:evaluate": "covered by `test_historic_integration.py`, grant included",
    "historic:events": "covered by `test_historic_integration.py`, grant included",
    "historic:timestamp": "covered by `test_historic_integration.py`, grant included",
    "router:quote": "builds a real quote against the chain, ~15 s on this hardware",
    "router:group": "builds a real transaction group; belongs with the swap tests",
    "router:sweep": "covered by `test_dustsweep_integration.py`, grant included",
}


def _manifest(name):
    """Return a widget's parsed manifest.

    :param name: the widget's module name
    :type name: str
    :return: :class:`widgethost.manifest.Manifest`
    """
    return importlib.import_module(f"widgets.inhouse.{name}.manifest").MANIFEST


def _engine_backed():
    """Return every widget that declares engine endpoints, by name.

    Discovered rather than listed, so a widget added to `WIDGETS` is covered
    without anything else being remembered.

    :return: list of (name, manifest)
    """
    return [
        (name, _manifest(name))
        for name in WIDGETS
        if _manifest(name).engine_endpoints
    ]


class WidgetScopeGrantTest(TestCase):
    """Each widget's read scopes, called the way that widget calls them."""

    def test_integration_every_widget_that_reads_holdings_may(self):
        """**One 403 per widget is invisible until a reader presses a button.**

        The deployment credential is granted per scope, and nothing else in
        this stack calls `account:holdings` on behalf of `haystack`, `folks` or
        `hogswap` - so a missing grant for any of them would be found by a
        reader rather than by CI.
        """
        refused, checked = {}, set()
        for name, manifest in _engine_backed():
            if "account:holdings" not in manifest.engine_endpoints:
                continue
            checked.add(name)
            try:
                holdings = fetch_account_holdings(
                    LINKED_ADDRESS, manifest.engine_endpoints
                )
            except BackendError as error:
                refused[name] = str(error)
                continue
            if not isinstance(holdings, dict):
                refused[name] = f"answered {type(holdings).__name__}, not a mapping"

        self.assertEqual(
            checked,
            EXPECTED_READERS,
            "the loop did not reach the widgets it is here for - an empty "
            "`refused` below would have meant nothing",
        )
        self.assertEqual(
            refused,
            {},
            "widgets whose own manifest could not read holdings: a 403 here is "
            "an ungranted scope, a `BackendError` about declaration is a "
            "manifest that drifted from the views",
        )

    def test_integration_every_widget_that_looks_assets_up_may(self):
        """The same question for the other shared read scope."""
        refused, checked = {}, set()
        for name, manifest in _engine_backed():
            if "assets:lookup" not in manifest.engine_endpoints:
                continue
            checked.add(name)
            try:
                matches = fetch_asset_matches(
                    KNOWN_QUERY, manifest.engine_endpoints
                )
            except BackendError as error:
                refused[name] = str(error)
                continue
            if not isinstance(matches, list):
                refused[name] = f"answered {type(matches).__name__}, not a list"

        self.assertEqual(checked, EXPECTED_READERS, "the loop reached nothing")
        self.assertEqual(refused, {}, "widgets whose own manifest could not search")

    def test_integration_a_scope_a_widget_did_not_declare_is_refused(self):
        """**The local half of the check, and it runs without the engine.**

        `engine_request` refuses before it sends, so a widget that calls a
        scope it forgot to declare fails here rather than spending the
        deployment credential on something its manifest does not admit.
        """
        alerts = _manifest("alerts")

        with self.assertRaises(BackendError):
            fetch_asset_matches(KNOWN_QUERY, alerts.engine_endpoints)

    def test_integration_every_engine_backed_scope_is_accounted_for(self):
        """**The guard that stops this file going quietly out of date.**

        A fifth widget, or a sixth scope on an existing one, is otherwise added
        and simply not tested - and nothing says so. Every declared scope has
        to be either exercised above or excused by name, and an excuse is a
        line somebody has to write.
        """
        unaccounted = {}
        for name, manifest in _engine_backed():
            missing = [
                scope
                for scope in manifest.engine_endpoints
                if scope not in EXERCISED and scope not in EXCUSED
            ]
            if missing:
                unaccounted[name] = sorted(missing)

        self.assertEqual(
            unaccounted,
            {},
            "scopes neither exercised nor excused. Add a call to EXERCISED if "
            "it is a harmless read, or a reason to EXCUSED if it is not",
        )

    def test_integration_no_excuse_outlives_the_scope_it_excuses(self):
        """An excuse for a scope nothing declares any more is a note about a
        world that has moved on, and reads as coverage that does not exist."""
        declared = {
            scope for _, manifest in _engine_backed() for scope in manifest.engine_endpoints
        }

        self.assertEqual(
            sorted(set(EXCUSED) - declared),
            [],
            "excuses for scopes no widget declares any more",
        )

    def test_integration_a_public_widget_declares_no_engine_endpoints(self):
        """**The manifest rule, checked against the deployed manifests.**

        `validate_manifest` forbids `public` with `engine_endpoints`, and both
        `alerts` and `liverefresh` rest on it: they claim to spend none of the
        deployment credential, and that claim is what lets a fork host them.
        """
        offenders = {
            name: sorted(manifest.engine_endpoints)
            for name in WIDGETS
            for manifest in [_manifest(name)]
            if manifest.capability == "public" and manifest.engine_endpoints
        }

        self.assertEqual(offenders, {}, "public widgets declaring engine scopes")
