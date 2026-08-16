"""Integration tests for the deployment-capabilities seam.

``core.context_processors.deployment_capabilities`` runs on every render, and
its failure path is silent by design::

    except (BackendError, Exception):  # noqa: BLE001 - never break rendering
        caps = {"permission": 0}

A backend that is down, misconfigured or unreachable therefore produces a
perfectly healthy-looking site with every tier gate closed -- ``Historic data``
and ``CSV export`` simply do not render, and nothing raises. That is the right
behaviour for a visitor and a poor one for a test suite: the rest of the tests
run with the engine unmocked and unreachable, so they all observe the stub, and
none of them can tell the difference between "this deployment is not entitled"
and "the backend never answered".

These tests are the only place the real value is asserted. They belong in
integration_tests precisely because they need the live backend that
conftest.py starts.

The cache matters here. Capabilities are cached for five minutes under a fixed
key, so a stub cached by an earlier failing run would satisfy a later passing
one. Every test clears it first.
"""

from django.core.cache import cache
from django.test import TestCase

from api.client import fetch_capabilities
from core.context_processors import _CACHE_KEY, deployment_capabilities

#: The stub the context processor substitutes when the backend cannot be
#: reached. Asserting against it by value keeps these tests honest: if the
#: fallback shape changes, they should be updated deliberately.
UNREACHABLE_STUB = {"permission": 0}


class DeploymentCapabilitiesTest(TestCase):
    """Testing class for capabilities fetched from the live backend."""

    def setUp(self):
        cache.delete(_CACHE_KEY)

    def test_integration_capabilities_endpoint_answers(self):
        """The backend must serve /api/v2/capabilities/ at all."""
        caps = fetch_capabilities()

        self.assertIsInstance(caps, dict, f"expected a mapping, got {caps!r}")
        self.assertIn(
            "permission",
            caps,
            "capabilities carry no 'permission' key, so every tier gate on "
            f"every page closes regardless of entitlement: {caps!r}",
        )

    def test_integration_capabilities_are_not_the_unreachable_stub(self):
        """A real permission, not the value that means "backend was down".

        This is the assertion the rest of the suite cannot make. If the live
        backend answers with permission 0 this test is wrong to fail -- but
        then the deployment genuinely is unentitled, which is worth knowing
        explicitly rather than inferring from missing links.
        """
        caps = fetch_capabilities()

        self.assertNotEqual(
            caps,
            UNREACHABLE_STUB,
            "the live backend returned exactly the stub the context processor "
            "substitutes on failure. Either this deployment has no "
            "entitlement, or the call failed and was swallowed -- from the "
            "page alone the two are indistinguishable, which is why this test "
            "exists.",
        )
        self.assertGreater(
            caps["permission"],
            0,
            f"permission is {caps['permission']}, so every gated feature is "
            "hidden site-wide",
        )

    def test_integration_context_processor_publishes_live_capabilities(self):
        """What the backend says must be what templates see."""
        expected = fetch_capabilities()
        cache.delete(_CACHE_KEY)

        context = deployment_capabilities(request=None)

        self.assertEqual(
            context["deployment_capabilities"],
            expected,
            "the context processor did not publish what the backend returned",
        )

    def test_integration_capabilities_are_cached_between_renders(self):
        """The five-minute cache has to actually hold what it fetched.

        This ran against DummyCache once and could not pass: the suite
        discarded every cache write, so `deployment_capabilities` made a live
        HTTP call on every render of every page. config.settings.automated_tests
        now gives the suite a real in-memory cache, and this test is what
        proves it -- revert that setting and this fails, loudly, instead of the
        backend quietly taking one request per page load again.
        """
        cache.delete(_CACHE_KEY)
        published = deployment_capabilities(request=None)

        self.assertEqual(
            cache.get(_CACHE_KEY),
            published["deployment_capabilities"],
            "capabilities were not cached, so each render re-requests them "
            "from the backend",
        )

    def test_integration_a_rendered_page_carries_live_capabilities(self):
        """End to end: request a real page and read what it was given."""
        caps = fetch_capabilities()
        cache.delete(_CACHE_KEY)

        response = self.client.get("/tokenomics/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["deployment_capabilities"],
            caps,
            "a rendered page did not receive the live capabilities, so what "
            "the gates decide on the page differs from what the backend says",
        )
