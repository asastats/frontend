"""Integration tests for the API token page, end to end against the backend.

``profile_api.html`` exists to hand a reader two JWTs. Everything else about
the page can be, and now is, tested without leaving the process -- the tier
gate, the empty state, the copy controls -- and none of it answers the only
question that matters: **does the token it just gave away actually work?**

That question spans three components and cannot be asked from any one of them.
The page mints the pair with ``RefreshToken.for_user``. DRF validates it with
``JWTStatelessUserAuthentication`` against ``SIMPLE_JWT_KEY``. The view behind
the endpoint then calls the engine and returns a live evaluation. A signing key
that drifts, an authentication class that changes, an endpoint that starts
refusing stateless users -- each of those leaves the page rendering two
perfectly formatted, perfectly useless strings, and every existing test passes.

``test_api_integration.py`` covers the same endpoints with
``settings.WIDGETS_API_TOKEN``, which is a different credential taking a
different path. Nothing anywhere used a token a *reader* was actually given.

.. note::
   ``api.permissions.CanAccessApiPermission.has_permission`` currently
   ``return True`` with a FIXME to reinstate the tier check and move from
   ``JWTStatelessUserAuthentication`` to ``JWTAuthentication``. These tests
   assert what the system does today, so
   :meth:`test_integration_the_api_does_not_yet_enforce_the_tier` documents the
   gap rather than pretending it is closed -- and will fail, loudly and in the
   right place, on the day that FIXME is addressed.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

#: The light mainnet address the other integration modules use.
LIGHT_ADDRESS = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M"

ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]


def _subscriber(username, permission=ASASTATSER):
    """Create a signed-in client for a reader whose tier reaches the page.

    ``force_login``: the ``user_logged_in`` receiver refreshes votes and
    permission for an authorized profile, which would go out to the permission
    dApp and overwrite the tier under test.

    :return: tuple of (:class:`Client`, :class:`User`)
    """
    user = get_user_model().objects.create(
        username=username, email=f"{username}@example.com"
    )
    user.profile.permission = permission
    user.profile.save()

    client = Client()
    client.force_login(user)
    return client, user


def _obtain_pair(client):
    """Ask the page for a token pair, the way the reader's button does.

    Read out of the response context rather than scraped from the HTML: what is
    under test is the token, and a markup change should not be able to break
    this module.

    :return: tuple of (refresh, access) as strings
    """
    response = client.get(f"{reverse('profile_api')}?refresh=yes")
    return response.context["refresh"], response.context["access"]


class ApiTokenIssueTest(TestCase):
    """The page mints a pair, and the pair is real."""

    def test_integration_the_page_hands_out_two_distinct_tokens(self):
        client, _ = _subscriber("token-issue")

        refresh, access = _obtain_pair(client)

        self.assertTrue(refresh)
        self.assertTrue(access)
        self.assertNotEqual(refresh, access, "the page handed out one token twice")
        # Three dot-separated segments: a JWT, not an opaque string the
        # endpoint would reject before any of this could be observed.
        for name, token in (("refresh", refresh), ("access", access)):
            with self.subTest(token=name):
                self.assertEqual(3, len(str(token).split(".")))

    def test_integration_obtaining_a_new_pair_gives_a_different_one(self):
        """The page warns that this invalidates the tokens above.

        The least it must do is issue different ones; a page that returned the
        same pair would make that warning a lie in the safest possible way.
        """
        client, _ = _subscriber("token-reissue")

        first_refresh, first_access = _obtain_pair(client)
        second_refresh, second_access = _obtain_pair(client)

        self.assertNotEqual(first_refresh, second_refresh)
        self.assertNotEqual(first_access, second_access)


class ApiTokenUsageTest(TestCase):
    """The pair, used against the endpoints the page sends the reader to."""

    def setUp(self):
        super().setUp()
        self.client_page, self.user = _subscriber("token-usage")
        self.refresh, self.access = _obtain_pair(self.client_page)
        self.api = APIClient()

    def _authorized(self, token):
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return self.api

    def test_integration_the_access_token_reaches_a_live_evaluation(self):
        """The whole point of the page, in one call.

        Not merely a 200: the payload has to be a real evaluation from the
        engine, because an authenticated request that returned an empty
        envelope would satisfy a status-code assertion and be worth nothing to
        the reader who came for their data.
        """
        response = self._authorized(self.access).get(f"/api/v2/{LIGHT_ADDRESS}/")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual([LIGHT_ADDRESS], response.data["account_info"]["addresses"])
        self.assertTrue(response.data["asaitems"], "no assets came back")
        self.assertTrue(float(response.data["total"]["total"]) > 0)

    def test_integration_the_api_and_the_page_agree_about_positions(self):
        """One payload, two consumers, one set of position ids.

        The API annotates in ``AsaItemSerializer.to_representation`` and the
        page in ``api.main.fetch_and_serialize_account``. Two annotation sites
        is a drift risk worth pinning: if they ever disagree, a pin made on the
        page would not name the position the API reports, and nothing else
        would notice.
        """
        from api.main import fetch_and_serialize_account

        api_response = self._authorized(self.access).get(f"/api/v2/{LIGHT_ADDRESS}/")
        page_payload = fetch_and_serialize_account(LIGHT_ADDRESS, LIGHT_ADDRESS)

        def ids(asaitems):
            return sorted(
                (item["asset"]["id"], program.get("pid"))
                for item in asaitems
                for program in (item.get("programs") or [])
            )

        self.assertEqual(
            ids(page_payload["asaitems"]),
            ids(api_response.data["asaitems"]),
            "the page and the API disagree about position identities",
        )

    def test_integration_the_refresh_token_mints_a_working_access_token(self):
        """The half of the pair the page describes as "use this one later".

        A refresh flow that returns a token which then fails is the one failure
        the reader cannot diagnose: their first token worked.
        """
        refreshed = self.api.post(
            "/api/v2/token/refresh/", {"refresh": str(self.refresh)}, format="json"
        )

        self.assertEqual(status.HTTP_200_OK, refreshed.status_code)
        new_access = refreshed.data["access"]
        self.assertNotEqual(str(self.access), new_access)

        response = self._authorized(new_access).get(f"/api/v2/{LIGHT_ADDRESS}/")

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(response.data["asaitems"])

    def test_integration_no_token_is_refused(self):
        """The gate is real, so the token above means something."""
        response = APIClient().get(f"/api/v2/{LIGHT_ADDRESS}/")

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_integration_a_forged_token_is_refused(self):
        """Signed with nothing, so `SIMPLE_JWT_KEY` is what did the work."""
        response = self._authorized("not.a.token").get(f"/api/v2/{LIGHT_ADDRESS}/")

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_integration_the_api_does_not_yet_enforce_the_tier(self):
        """Documents the FIXME in `api.permissions.CanAccessApiPermission`.

        `has_permission` returns True unconditionally, so a token minted for a
        reader below Asastatser is accepted -- even though the *page* that
        mints it is gated. That is the current behaviour and it is asserted
        here rather than left implicit, so reinstating the check fails this
        test and nothing else, which is exactly where the news belongs.
        """
        client, _ = _subscriber("token-untiered", permission=0)
        # The page itself refuses them, so the token is minted directly the way
        # the view does -- the question is what the *endpoint* does with it.
        from rest_framework_simplejwt.tokens import RefreshToken

        access = RefreshToken.for_user(
            get_user_model().objects.get(username="token-untiered")
        ).access_token

        # The page turns them away -- that gate is real and is what makes the
        # endpoint's silence below the interesting half.
        page = client.get(reverse("profile_api"))
        self.assertEqual(status.HTTP_302_FOUND, page.status_code)

        response = self._authorized(str(access)).get(f"/api/v2/{LIGHT_ADDRESS}/")

        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code,
            "the API now enforces the tier -- good. Update this test and the "
            "note in the module docstring; the FIXME in api/permissions.py is "
            "done.",
        )
