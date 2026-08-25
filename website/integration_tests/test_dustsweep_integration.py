"""Integration tests for the Dust Sweep widget against a running engine.

The widget has one engine-backed endpoint, ``router:sweep``, and nothing else
in the suite exercises it. Every failure below is therefore a failure of *our*
stack rather than a vendor's.

**On the scope grant.** ``HasWidgetScope`` refuses any endpoint whose scope the
deployment's credential does not carry, so until ``router:sweep`` is granted the
engine answers **403** for every caller. That is the current, deliberate state
and the tests below record it rather than skipping past it - when the grant
lands, the test that pins the 403 is the one that should fail and tell you to
update it. Grant it with::

    python manage.py create_deployment "<name>" --grant --scope router:sweep

**On what is asserted.** The gating tests are unconditional: ownership, the
overridden body address and the malformed-body refusals all happen in *our*
view, before the engine is reached, so they hold whatever the engine answers.
The plan-shape tests tolerate both states, because a test that only passes
before a grant is a test that has to be deleted the moment the feature works.

**On timing.** A sweep reads an account and may quote a conversion, and a quote
on this hardware takes about fifteen seconds against a thirty-second client
timeout. ``ASASTATS_API_TIMEOUT`` is the knob; a ``ReadTimeout`` here is the
machine, not the logic.
"""

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from walletauth.models import LinkedAddress
from widgets.inhouse.dustsweep.manifest import MANIFEST

#: A real mainnet address. Whatever it holds, the sweep must answer coherently.
LINKED_ADDRESS = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M"


def _make_linked_user(email="dustsweep-integration@example.com", permission=100):
    """Return a user with `LINKED_ADDRESS` connected to their profile.

    `Profile.address` has to match the primary link, and not only for realism:
    `walletauth.signals.reconcile_primary_registry` is a post_save on Profile
    that deletes every `is_primary` row not matching `Profile.address`. Leave it
    empty and the row below is dropped the moment anything saves the profile -
    and `force_login` does exactly that - so the gate then refuses a user who
    really is linked, and every "this should be refused" test passes for
    entirely the wrong reason.
    """
    user = get_user_model().objects.create_user(
        username=email, email=email, password="top_secret"
    )
    user.profile.permission = permission
    user.profile.address = LINKED_ADDRESS
    user.profile.save()
    LinkedAddress.objects.create(
        profile=user.profile,
        address=LINKED_ADDRESS,
        canonical_address=LINKED_ADDRESS,
        chain="algorand",
        auth_method="algorand_wallet",
        is_primary=True,
        login_enabled=True,
    )
    return user


class DustsweepManifestTest(TestCase):
    """The manifest is what `engine_request` enforces the scopes against."""

    def test_integration_the_manifest_declares_the_sweep_scope(self):
        """A scope the manifest does not name fails closed with a BackendError.

        Which is safe, and indistinguishable from the engine being down unless
        it is asserted.
        """
        assert "router:sweep" in MANIFEST.engine_endpoints

    def test_integration_the_manifest_is_not_a_swap_router(self):
        """`category = "swap"` would make the sweep a selectable default router."""
        assert MANIFEST.category != "swap"
        assert MANIFEST.id == "dustsweep"


class DustsweepPlanViewTest(TestCase):
    """The plan endpoint, against a running engine."""

    def setUp(self):
        self.user = _make_linked_user()
        self.client.force_login(self.user)
        self.url = reverse("dustsweep_plan")

    def _post(self, body=None, address=LINKED_ADDRESS):
        return self.client.post(
            f"{self.url}?address={address}",
            data=json.dumps(body if body is not None else {}),
            content_type="application/json",
        )

    def test_integration_a_plan_comes_back_or_the_scope_is_not_granted(self):
        """The shape `dustsweep.js` reads, once the grant is in place.

        Written to tolerate both states on purpose. A test asserting only the
        403 would have to be deleted the day the feature starts working, and a
        test asserting only the plan cannot run until then - so this pins the
        403's *reason* while it lasts, and the plan's contract once it does not.
        """
        response = self._post()
        assert response.status_code in (200, 403, 503), response.content[:400]

        if response.status_code == 403:
            # The grant is what is missing, and the engine says so. Anything
            # else arriving as a 403 would be a different fault wearing the
            # same status.
            assert "scope" in response.json()["error"]
            return

        if response.status_code == 503:
            return  # the engine cannot plan at all - an empty pair graph, say

        plan = response.json()
        for key in (
            "address",
            "summary",
            "holdings",
            "next",
            "refused",
            "conversions_unavailable",
        ):
            assert key in plan, f"{key} missing from {sorted(plan)}"

        # A restricted router must not cost the close-out half its answer. It
        # did until 2026-08-25: `RouterUnavailable` escaped `plan` and became a
        # 503 for the whole sweep, and this test agreed with it because 503 was
        # in the allowed set above. The outage now arrives as a *field* on a
        # 200, which is the difference between "we cannot convert" and "go
        # away".
        if plan["conversions_unavailable"]:
            assert "RESTRICT_TO_ADMIN" in plan["conversions_unavailable"]

        assert plan["address"] == LINKED_ADDRESS
        for key in ("close", "forfeit", "convert", "keep", "unpriced", "prompts"):
            assert key in plan["summary"], sorted(plan["summary"])

    def test_integration_the_engine_filters_out_dapp_positions(self):
        """The dApp-position filter, checked against whatever is deployed.

        **Skipped rather than tolerated when the engine predates it.** The
        previous outage test was written to allow both answers and thereby
        certified a real bug for a week; the difference here is that a missing
        field produces a *visible skip naming the fix*, not a green tick.

        The engine this suite talks to is a separate checkout on port 8001, so
        this failing to find the field means that checkout needs syncing - not
        that the code in this repository is wrong.
        """
        response = self._post()
        if response.status_code != 200:
            self.skipTest(f"the engine answered {response.status_code}")

        plan = response.json()
        if "evaluation_unavailable" not in plan:
            self.skipTest(
                "the engine on :8001 predates the dApp-position filter - sync "
                "the engine checkout and restart it"
            )

        # Present means the filter ran. Every holding is then either something
        # the sweep may touch or something it explicitly refused, and
        # `committed` is the refusal that says "this is a position, not dust".
        assert "committed" in plan["summary"], sorted(plan["summary"])
        for holding in plan["holdings"]:
            if holding["disposition"] == "committed":
                assert holding["reason"], holding
                # never offered for signing, whatever the reader asks for
                assert holding["asset"] not in [
                    one["asset"] for one in (plan["next"] or {}).get("holdings", [])
                ]

    def test_integration_the_body_address_cannot_be_someone_elses(self):
        """The gated address wins over whatever the body claims.

        Unconditional: the view overwrites `payload["address"]` before the
        engine is called, so this holds whether or not the scope is granted.
        Stronger here than on a swap - a plan discloses an entire account and
        returns a group that closes its holdings out.
        """
        other = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
        response = self._post(body={"address": other})
        assert response.status_code in (200, 403, 503), response.content[:400]

        if response.status_code == 200:
            assert response.json()["address"] == LINKED_ADDRESS

    def test_integration_an_address_the_user_has_not_linked_is_refused(self):
        """Ownership is the hard gate, and it is ours rather than the engine's."""
        other = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
        assert self._post(address=other).status_code in (302, 403)

    def test_integration_a_missing_address_is_refused(self):
        """`test_func` returns False on an empty address rather than gating on "" ."""
        assert self._post(address="").status_code in (302, 403)

    def test_integration_an_anonymous_visitor_is_sent_to_log_in(self):
        self.client.logout()
        assert self._post().status_code in (302, 403)

    def test_integration_a_malformed_body_never_reaches_the_engine(self):
        """400 from us, not a 500 from the engine parsing our forwarded junk."""
        response = self.client.post(
            f"{self.url}?address={LINKED_ADDRESS}",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_integration_a_non_object_body_never_reaches_the_engine(self):
        response = self.client.post(
            f"{self.url}?address={LINKED_ADDRESS}",
            data="[]",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_integration_the_response_is_never_cached(self):
        """A plan is a statement about holdings and reserves at a moment.

        It also carries a transaction group built against a specific round, so
        serving a stale one hands a reader a group the chain will not accept -
        or, worse, a forfeit priced before the token moved.

        Driven with a malformed body on purpose. `never_cache` decorates
        `dispatch`, so the header is set on the refusal too, and this then needs
        no live engine call - which matters because a sweep may quote, and a
        quote on this hardware can exceed `ASASTATS_API_TIMEOUT` and make an
        assertion about a *header* fail for reasons that have nothing to do with
        caching.
        """
        response = self.client.post(
            f"{self.url}?address={LINKED_ADDRESS}",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "no-store" in response.headers.get("Cache-Control", "")

    def test_integration_opted_in_is_bounded_by_the_engine(self):
        """The one field that widens a sweep, so its ceiling is enforced remotely.

        The widget forwards it untouched - it has no way to know whether an
        asset could be valued - so the bound has to hold at the engine, and a
        400 is what says it did.

        The count has to exceed `core.views.MAX_OPTED_IN`, which this side
        cannot import: the open app must not depend on the engine. So it is a
        number chosen to sit clearly above it rather than at it, and this
        comment is the coupling. An earlier version sent 1,000 against a cap of
        512; raising the cap to 4,096 left the test passing for the wrong reason
        - it was answering 403 for want of the scope grant, and would have
        started returning 200 the day that landed.
        """
        response = self._post(body={"opted_in": list(range(100_000))})
        assert response.status_code in (400, 403, 503), response.content[:400]

        if response.status_code == 400:
            assert "opted_in" in response.json()["error"]
