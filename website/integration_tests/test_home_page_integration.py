"""Integration tests for home and the bundle-name forms, against the backend.

These pages hold no backend call of their own -- a bundle list is a database
query -- so it is fair to ask what there is to integrate. The answer is that
home is where a bundle is *made*, and the address page is where the engine is
asked to evaluate it. The two are joined by a hash the website computes and the
engine recomputes, and by a name-to-addresses resolution that lives in the
website's cache. Neither side is tested against the other by anything else:

* ``bundle_from_addresses`` produces the hash home renders into every historic
  link and every evaluation URL;
* ``check_bundle_addresses`` turns that hash back into an address list;
* ``BaseAddressView`` hands that list to the engine, which cross-checks the
  hash it was given against the addresses it was given.

So a bundle created through the form and followed through the link the page
renders is the one flow that crosses all of it. The unit tests mock the engine;
the functional tests mock the engine; a hash that stopped agreeing would pass
both and fail for every reader on the day it shipped.

The bundle used here is deliberately **two real mainnet addresses**, because a
single-address bundle takes a different branch in ``dispatch`` -- the url value
*is* the address list, and no hash is resolved at all.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse, resolve

from core.models import BundleName
from utils.helpers import bundle_from_addresses, check_bundle_addresses

#: Two light mainnet addresses. Small enough to evaluate inside the backend read
#: timeout, and two of them so the bundle branch is the one under test.
FIRST = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M"
SECOND = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


def _reader(username="home-integration"):
    """Create a signed-in client for a reader with a tier that clears the gates.

    ``force_login``: the ``user_logged_in`` receiver refreshes votes and
    permission for an authorized profile, which would reach the permission dApp
    and overwrite the tier under test.

    :return: tuple of (:class:`Client`, :class:`User`)
    """
    user = get_user_model().objects.create(
        username=username, email=f"{username}@example.com"
    )
    user.profile.permission = 258_885_438_200  # Professional
    user.profile.save()

    client = Client()
    client.force_login(user)
    return client, user


class BundleRoundTripTest(TestCase):
    """A bundle made on these pages is a bundle the engine can evaluate."""

    def setUp(self):
        super().setUp()
        self.client_page, self.user = _reader()

    def _create(self, name="Integration bundle"):
        """Create a bundle through the form, as a reader does."""
        response = self.client_page.post(
            reverse("bundlename_add"),
            {"name": name, "addresses": f"{FIRST} {SECOND}"},
        )
        self.assertEqual(302, response.status_code, "the form did not accept the bundle")
        return BundleName.objects.get(profile=self.user.profile)

    def test_integration_the_form_stores_what_the_reader_typed(self):
        """Guard the guard: everything below follows this row."""
        bundle = self._create()

        self.assertEqual(sorted(bundle.addresses.split()), sorted([FIRST, SECOND]))
        self.assertEqual(2, bundle.size)

    def test_integration_home_links_to_a_hash_that_resolves_back(self):
        """The hash home renders is the one the site can turn into addresses.

        `bundle_from_addresses` computes it and `check_bundle_addresses` undoes
        it through the cache. If those two ever disagree, every historic link on
        this page leads to a bundle the site cannot resolve -- and both sides
        are the website's own code, so no mocked test would notice.
        """
        bundle = self._create()
        page = self.client_page.get(reverse("home")).content.decode()

        self.assertIn(bundle.bundle, page, "home renders a hash the bundle does not have")
        self.assertEqual(
            bundle.bundle, bundle_from_addresses(f"{FIRST} {SECOND}")
        )
        self.assertEqual(
            sorted(check_bundle_addresses(bundle.bundle).split()),
            sorted([FIRST, SECOND]),
            "the hash home rendered does not resolve back to its addresses",
        )

    def test_integration_following_the_evaluation_link_reaches_the_engine(self):
        """The whole point of the page, end to end.

        Home renders a link per bundle; this follows it and requires a real
        evaluation to come back. A 200 alone would be satisfied by a page that
        rendered nothing, which is what a broken hash produces: the view
        redirects to the index rather than raising.
        """
        bundle = self._create()
        page = self.client_page.get(reverse("home")).content.decode()
        self.assertIn(f'href="/{bundle.name}"', page)

        # Followed, because the name is a redirect: `BundleNameView` looks the
        # bundle up, caches the hash with `create_bundle`, and sends the reader
        # to the bundle page. That hop *is* the chain -- name to hash to engine
        # -- so a test that stopped at the 302 would leave all of it untested.
        response = self.client_page.get(f"/{bundle.name}", follow=True)

        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "address.html")
        self.assertEqual(
            f"/{bundle.bundle}",
            response.redirect_chain[-1][0],
            "the name resolved to something other than its own bundle hash",
        )
        account = response.context["account"]
        self.assertTrue(
            response.context["is_bundle"],
            "the bundle link resolved to the single-address branch",
        )
        self.assertEqual(
            sorted(account["account_info"]["addresses"]),
            sorted([FIRST, SECOND]),
            "the engine evaluated a different address list than the bundle holds",
        )
        self.assertTrue(account["asaitems"], "no assets came back for the bundle")

    def test_integration_a_bundle_evaluates_to_the_sum_of_its_addresses(self):
        """Two addresses in, one portfolio out.

        The cross-check that makes the bundle branch worth its own test: the
        engine is handed a hash *and* a list, and a bundle whose total ignored
        one of its addresses would still render a perfectly healthy page.
        """
        bundle = self._create()

        together = self.client_page.get(f"/{bundle.name}", follow=True).context["account"]
        first = self.client_page.get(f"/{FIRST}").context["account"]
        second = self.client_page.get(f"/{SECOND}").context["account"]

        self.assertAlmostEqual(
            float(together["total"]["total"]),
            float(first["total"]["total"]) + float(second["total"]["total"]),
            delta=0.5,
            msg="the bundle total is not its addresses' totals",
        )

    def test_integration_the_historic_link_points_at_a_real_route(self):
        """It is built from the hash, so a wrong hash is a dead link.

        Resolved rather than followed: the widget processes on a queue and
        opening it here would start work no test can wait for.
        """
        bundle = self._create()
        page = self.client_page.get(reverse("home")).content.decode()

        target = reverse("historic", args=[bundle.bundle])
        self.assertIn(target, page)
        self.assertEqual("historic", resolve(target).url_name)

    def test_integration_the_edit_form_round_trips_the_addresses(self):
        """What the reader typed is what the form gives back.

        The addresses are stored as one string and re-rendered into a textarea;
        a normalisation that ran on save but not on load would quietly rewrite a
        reader's bundle the next time they pressed Update.
        """
        bundle = self._create()

        response = self.client_page.get(
            reverse("bundlename_edit", args=[bundle.name])
        )

        self.assertEqual(200, response.status_code)
        form = response.context["form"]
        self.assertEqual(
            sorted(form.initial["addresses"].split()), sorted([FIRST, SECOND])
        )

    def test_integration_every_page_carries_this_deployments_capabilities(self):
        """`deployment_capabilities` runs on every render and fails silently.

        Its except arm returns a zero-permission stub, so a backend that is down
        produces a healthy-looking page with every tier gate closed. On these
        pages that is the Historic link disappearing from every row. Nothing
        else here asserts the live value.
        """
        from django.core.cache import cache

        cache.delete("deployment_capabilities")
        self._create()

        response = self.client_page.get(reverse("home"))

        caps = response.context["deployment_capabilities"]
        self.assertIn("permission", caps)
        self.assertNotEqual(
            {"permission": 0},
            caps,
            "the capabilities are the unreachable-backend stub, so this whole "
            "run was against a backend that did not answer",
        )
