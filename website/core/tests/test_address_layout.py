"""Resolving a reader's layout, and why it cannot be rendered into the page.

:func:`utils.layouts.layout_for_user` answers "which layout does this reader
get". :class:`TestCachedPageIsSharedBetweenReaders` is why the answer may not
be written into ``address.html``.

**The address page's cache is shared between signed-in readers.**
``cache_page`` is a *view* decorator, so it runs inside the middleware stack.
``SessionMiddleware`` adds ``Vary: Cookie`` in its ``process_response``, which
happens *after* ``learn_cache_key`` has already recorded which headers to key
on -- so the entry is stored without varying on the cookie, and the
``Vary: Cookie`` visible on the finished response plays no part in the lookup.
Two readers, two sessions, one cache entry.

That is the constraint :class:`core.views.SwapEntryView` was built around, and
the reason its per-user config arrives as a separate non-cached partial. The
layout has to arrive the same way.

Two traps to know about before changing any of this:

* **The settings module decides whether the bug is even visible.**
  ``config.settings.development`` uses ``DummyCache``, under which nothing is
  cached and every reader looks correctly isolated. ``frontend/pytest.ini``
  pins ``--ds=config.settings.automated_tests`` (LocMemCache) so the suite sees
  real caching -- a probe run outside that rootdir does not, and will happily
  report that there is no problem.
* **Anonymous-then-authenticated proves nothing.** That pair passes even with
  the bug, because the first request populates the entry and the second is a
  different reader only by luck of ordering. Two *signed-in* readers is the
  case that discriminates.
"""

import json
from pathlib import Path
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

from core.views import BaseAddressView
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from utils.layouts import layout_for_user

ADDRESS = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"

#: The real bundle payload, so the page renders its full asset list rather than
#: a trimmed stand-in that might not reach the position component at all.
SAMPLE = Path(__file__).parent.parent.parent / "utils/tests/sample_serialized_540A5.json"


@pytest.fixture(scope="module")
def payload():
    """The captured serialized account payload."""
    return json.loads(SAMPLE.read_text())


def _render_patches(payload):
    """Return the collaborator patches an address-page render needs.

    Three of these reach outside the process -- the export status and the
    capabilities context processor both call the API on :8001, and the banner
    picks a sponsor -- and none of them has anything to do with layout. The
    capabilities call is memoized, so without patching it only the test that
    happens to run on a cold cache fails, which is worse than all of them
    failing.

    :param payload: serialized account payload to serve
    :type payload: dict
    :return: tuple of context managers
    """
    return (
        mock.patch("core.views.fetch_and_serialize_account", return_value=payload),
        mock.patch("core.views.check_export_status", return_value={}),
        mock.patch("core.views.weighted_randomized_banner", return_value=None),
        mock.patch("core.context_processors.fetch_capabilities", return_value={}),
    )


def _user(username, permission=0, layout=""):
    """Create a user whose profile carries ``permission`` and ``layout``.

    :return: :class:`User`
    """
    user = get_user_model().objects.create(username=username, email=f"{username}@e.com")
    user.set_password("12345o")
    user.save()
    user.profile.permission = permission
    user.profile.preferred_layout = layout
    user.profile.save()
    return user


def _client_for(user):
    """Return a logged-in client for ``user``.

    The permission provider is patched out because ``login`` triggers a votes
    and permission refresh that would otherwise overwrite the tier under test.

    :return: :class:`Client`
    """
    client = Client()
    with mock.patch("core.models.get_permission_provider") as provider:
        provider.return_value.votes_and_permission.return_value = [
            0,
            user.profile.permission,
        ]
        client.login(username=user.username, password="12345o")
    return client


class TestLayoutResolution:
    """Who gets which layout, before anything renders it."""

    def test_anonymous_reader_gets_the_default(self):
        """Nothing to read and no tier to check, so nothing to decide."""
        assert layout_for_user(AnonymousUser()) == ("classic", "rows")

    @pytest.mark.django_db
    def test_signed_in_reader_gets_their_choice(self):
        user = _user(
            "layoutctx-1",
            permission=SUBSCRIPTION_TIER_PERMISSIONS["Intro"],
            layout="classic-compact",
        )

        assert layout_for_user(user) == ("classic-compact", "cards")

    @pytest.mark.django_db
    def test_lapsed_tier_falls_back(self):
        """The gate is re-checked on read, not only when the choice is saved."""
        user = _user("layoutctx-2", permission=0, layout="money-column")

        assert layout_for_user(user) == ("classic", "rows")


class TestCachedViewCarriesNoReaderState:
    """The address view must not resolve a layout at all.

    It did briefly, and the damage was not the leak -- it was that the context
    key existed, looked authoritative, and invited a template to use it.
    """

    def test_the_context_has_no_layout_keys(self, payload):
        view = BaseAddressView()
        request = RequestFactory().get(f"/{ADDRESS}")
        view.request = request
        view.args = (ADDRESS,)
        view.kwargs = {}
        view.addresses = ADDRESS
        p1, p2, p3, p4 = _render_patches(payload)
        with p1, p2, p3, p4:
            context = view.get_context_data()

        assert "layout" not in context
        assert "layout_position" not in context

    def test_the_view_does_not_read_the_user(self, payload):
        """A `RequestFactory` request has no `.user`, and that must be fine.

        The assertion is the absence of an `AttributeError`: reading the user
        here is precisely how per-reader state gets into a shared entry, so the
        view is expected to render without ever touching it.
        """
        view = BaseAddressView()
        view.request = RequestFactory().get(f"/{ADDRESS}")
        view.args = (ADDRESS,)
        view.kwargs = {}
        view.addresses = ADDRESS
        p1, p2, p3, p4 = _render_patches(payload)
        with p1, p2, p3, p4:
            context = view.get_context_data()

        assert context["url_value"] == ADDRESS


class TestMarkupDoesNotCarryTheReadersLayout:
    """The cached page ships one presentation, the same one for everybody.

    The opposite of what this module set out to assert. Kept as a guard: the
    obvious implementation is to interpolate ``layout_position`` into the
    component, and it renders correctly in every manual check, because the
    second reader only appears in production.
    """

    def _render(self, user, payload):
        """Return the rendered address page for ``user``."""
        p1, p2, p3, p4 = _render_patches(payload)
        with p1, p2, p3, p4:
            client = _client_for(user) if user else Client()
            return client.get(f"/{ADDRESS}").content.decode()

    @pytest.mark.django_db
    def test_the_component_ships_the_default_presentation(self, payload):
        cache.clear()
        html = self._render(None, payload)

        assert "position--rows" in html
        assert "position--cards" not in html

    @pytest.mark.django_db
    def test_a_compact_reader_still_gets_the_default(self, payload):
        """Not the desired behaviour -- the safe one, until it comes off the cache.

        A reader who chose the compact layout sees the default until the
        preference is delivered off the cached page. Wrong-but-shared beats
        right-for-whoever-loaded-it-first.
        """
        cache.clear()
        user = _user(
            "layoutmk-1",
            permission=SUBSCRIPTION_TIER_PERMISSIONS["Intro"],
            layout="classic-compact",
        )
        html = self._render(user, payload)

        assert "position--cards" not in html

    @pytest.mark.django_db
    def test_every_position_declares_a_presentation(self, payload):
        """A bare `.position` declares no grid areas, so its children overlap.

        Counted rather than sampled: the component has two branches, and the
        wallet's own ALGO balance goes through the one that is easy to forget.
        """
        cache.clear()
        html = self._render(None, payload)

        assert html.count('class="position position--') == html.count(
            'class="position position--rows"'
        )


@pytest.mark.django_db
class TestCachedPageIsSharedBetweenReaders:
    """The constraint that keeps per-reader state off this page.

    Not a wish -- a demonstration of current behaviour. Anything rendered into
    ``address.html`` is handed to whoever asks next, so the layout, and later
    the pins and the saved order, have to arrive off the cache.

    If these tests ever fail, the caching changed. That is good news, not a
    regression: check whether ``AddressView`` gained ``vary_on_cookie`` or moved
    to middleware-level caching, and if so this whole module can be simplified
    and the layout rendered inline after all. Do not "fix" them by weakening the
    assertion.
    """

    def test_two_readers_share_one_entry(self, payload):
        """The discriminating case: two *signed-in* readers, in order.

        Their sessions differ, their profiles differ, and the second is served
        the first's bytes. An anonymous-then-authenticated pair would pass here
        even though the bug is present, which is why that pairing is not the
        test.
        """
        cache.clear()
        first = _user("layoutiso-2", SUBSCRIPTION_TIER_PERMISSIONS["Intro"])
        second = _user("layoutiso-3", SUBSCRIPTION_TIER_PERMISSIONS["Intro"])
        p1, p2, p3, p4 = _render_patches(payload)
        with p1, p2, p3, p4:
            client_one = _client_for(first)
            first_html = client_one.get(f"/{ADDRESS}").content.decode()
            client_two = _client_for(second)
            second_html = client_two.get(f"/{ADDRESS}").content.decode()

        assert (
            client_one.cookies["sessionid"].value
            != client_two.cookies["sessionid"].value
        ), "the two clients shared a session; the test proves nothing"
        assert first_html == second_html, (
            "the address page no longer shares a cache entry between readers -- "
            "see this class's docstring before changing anything"
        )

    def test_the_vary_header_does_not_key_the_entry(self, payload):
        """`Vary: Cookie` is on the response and plays no part in the lookup.

        This is the whole trap in one assertion. ``cache_page`` is a view
        decorator, so ``learn_cache_key`` runs before ``SessionMiddleware``
        appends ``Vary: Cookie`` -- the header is on the finished response, and
        reading it as evidence of per-reader keying is exactly the mistake this
        module exists to stop someone repeating.
        """
        cache.clear()
        first = _user("layoutvary-1", SUBSCRIPTION_TIER_PERMISSIONS["Intro"])
        second = _user("layoutvary-2", SUBSCRIPTION_TIER_PERMISSIONS["Intro"])
        p1, p2, p3, p4 = _render_patches(payload)
        with p1, p2, p3, p4:
            one = _client_for(first).get(f"/{ADDRESS}")
            two = _client_for(second).get(f"/{ADDRESS}")

        assert "Cookie" in one.headers.get("Vary", "")
        assert one.content == two.content, "Vary now keys the entry; see the docstring"

    def test_the_suite_runs_with_caching_switched_on(self):
        """Guards the guard.

        ``config.settings.development`` uses ``DummyCache``, under which every
        test in this class passes vacuously and the page looks perfectly
        isolated. ``frontend/pytest.ini`` pins the automated-test settings for
        this reason; a probe run outside that rootdir does not get them.
        """
        from django.conf import settings

        backend = settings.CACHES["default"]["BACKEND"]

        assert "dummy" not in backend.lower(), (
            f"caching is disabled ({backend}); this module cannot detect anything"
        )
