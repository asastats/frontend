"""Resolving a reader's layout, and how the cache is keyed on it.

:func:`utils.layouts.layout_for_user` answers "which layout does this reader
get". :class:`TestCacheIsKeyedOnTheLayout` is why that answer may now be
rendered into the page, and :class:`TestCachedPageIsSharedWithinOneLayout` is
why nothing *else* about the reader may be.

**The address page's cache entry is shared between readers on the same
layout.** ``cache_page`` is a *view* decorator, so it runs inside the middleware
stack. ``SessionMiddleware`` adds ``Vary: Cookie`` in its ``process_response``,
which happens *after* ``learn_cache_key`` has already recorded which headers to
key on -- so the entry is stored without varying on the cookie, and the
``Vary: Cookie`` visible on the finished response plays no part in the lookup.
Two readers, two sessions, one cache entry.

The layout escapes that because :meth:`core.views.BaseAddressView.dispatch`
folds it into the cache *key prefix* rather than hoping a header will do it.
That is a deliberate choice over ``vary_on_cookie``, which would key on the
whole cookie and give every session its own entry -- correct, and useless.

Everything else about a reader still has to arrive off the cache. That is the
constraint :class:`core.views.SwapEntryView` was built around, and the reason
its per-user config is a separate non-cached partial.

Two traps to know about before changing any of this:

* **The settings module decides whether the bug is even visible.**
  ``config.settings.development`` uses ``DummyCache``, under which nothing is
  cached and every reader looks correctly isolated. ``frontend/pytest.ini``
  pins ``--ds=config.settings.automated_tests`` (LocMemCache) so the suite sees
  real caching -- a probe run outside that rootdir does not, and will happily
  report that there is no problem.
* **Anonymous-then-authenticated proves nothing.** That pair passes even with
  a leak, because the first request populates the entry and the second is a
  different reader only by luck of ordering. Two *signed-in* readers is the
  case that discriminates.
"""

import json
from pathlib import Path
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import Client, RequestFactory

from core.views import BaseAddressView
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from utils.layouts import layout_for_user

ADDRESS = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"

ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
INTRO = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]

#: The real bundle payload, so the page renders its full asset list rather than
#: a trimmed stand-in that might not reach the position component at all.
SAMPLE = (
    Path(__file__).parent.parent.parent / "utils/tests/sample_serialized_540A5.json"
)


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


def _render(user, payload):
    """Return the rendered address page for ``user`` (None for signed out).

    :return: str
    """
    p1, p2, p3, p4 = _render_patches(payload)
    with p1, p2, p3, p4:
        client = _client_for(user) if user else Client()
        return client.get(f"/{ADDRESS}").content.decode()


class TestLayoutResolution:
    """Who gets which layout, before anything renders it."""

    def test_anonymous_reader_gets_the_default(self):
        """Nothing to read and no tier to check, so nothing to decide."""
        assert layout_for_user(AnonymousUser()) == "classic"

    @pytest.mark.django_db
    def test_signed_in_reader_gets_their_choice(self):
        user = _user("layoutctx-1", permission=ASASTATSER, layout="dynamic")

        assert layout_for_user(user) == "dynamic"

    @pytest.mark.django_db
    def test_signed_in_reader_without_a_choice_gets_the_default(self):
        user = _user("layoutctx-3", permission=ASASTATSER)

        assert layout_for_user(user) == "classic"

    def test_a_user_with_no_profile_gets_the_default(self):
        """Signed in, but the profile row is missing.

        Rare and not impossible: a user created outside the signal that makes
        profiles -- a fixture, a data migration, a manual insert. The address
        page is the busiest on the site and must not 500 for them, so "no
        profile to ask" resolves the same way "nobody is asking" does.
        """

        class _Profileless:
            is_authenticated = True

        assert layout_for_user(_Profileless()) == "classic"

    def test_a_request_without_a_user_gets_the_default(self):
        """`AuthenticationMiddleware` absent, or a bare `RequestFactory`.

        The view passes `getattr(request, "user", None)`, so this is the value
        it hands over. Raising here would turn a middleware ordering change into
        a 500 on the address page.
        """
        assert layout_for_user(None) == "classic"

    @pytest.mark.django_db
    def test_lapsed_tier_falls_back(self):
        """The gate is re-checked on read, not only when the choice is saved."""
        user = _user("layoutctx-2", permission=0, layout="dynamic")

        assert layout_for_user(user) == "classic"


class TestCachedViewCarriesOnlyTheLayout:
    """The layout is the *only* reader-derived value this context may carry.

    It may carry that one because the cache key accounts for it. Nothing else
    about the reader is in the key, so nothing else may be in the context --
    their addresses, their router, their tier all belong to whoever asks next.
    """

    def _context(self, payload, layout="classic"):
        """Build the view's context directly, bypassing dispatch.

        :return: dict
        """
        view = BaseAddressView()
        view.request = RequestFactory().get(f"/{ADDRESS}")
        view.args = (ADDRESS,)
        view.kwargs = {}
        view.addresses = ADDRESS
        view.layout = layout
        p1, p2, p3, p4 = _render_patches(payload)
        with p1, p2, p3, p4:
            return view.get_context_data()

    def test_the_context_carries_the_layout(self, payload):
        assert self._context(payload, "dynamic")["layout"] == "dynamic"

    def test_the_context_carries_the_compact_flag(self, payload):
        assert self._context(payload, "dynamic-compact")["compact"] is True

    def test_the_compact_flag_is_false_for_a_full_layout(self, payload):
        assert self._context(payload, "dynamic")["compact"] is False

    def test_the_context_carries_nothing_else_about_the_reader(self, payload):
        """A `RequestFactory` request has no `.user`, and that must be fine.

        The assertion is the absence of an `AttributeError`. Reading the user
        inside `get_context_data` is precisely how per-reader state gets into a
        shared entry; the layout is resolved once in `dispatch`, where it can
        also reach the cache key, and never here.
        """
        context = self._context(payload)

        assert context["url_value"] == ADDRESS


@pytest.mark.django_db
class TestCacheIsKeyedOnTheLayout:
    """Two layouts, two entries -- and no path between them.

    The failure this replaces: the layout was a registry entry that rendered
    the same page, so choosing the new design changed nothing on screen. A
    layout that does not reach the markup is not a layout, and a layout that
    reaches the markup without reaching the cache key is a leak.
    """

    def test_readers_on_different_layouts_get_different_pages(self, payload):
        """The whole point. If these ever match, the layout stopped mattering."""
        cache.clear()
        money = _user("layoutkey-1", permission=ASASTATSER, layout="dynamic")
        classic = _user("layoutkey-2", permission=ASASTATSER, layout="classic")

        assert _render(money, payload) != _render(classic, payload)

    def test_a_subscribers_page_is_not_served_to_a_free_reader(self, payload):
        """A warmed paid entry must be unreachable from below the gate.

        The subscriber goes first *on purpose*: their render populates the
        `layout-dynamic` entry, and the free reader must miss it rather
        than inherit it. This is the shared-cache bug's shape, closed by
        construction -- the key prefix is built from the *normalized* layout, so
        an unentitled reader resolves to `classic` before a key exists.
        """
        cache.clear()
        subscriber = _user("layoutkey-3", permission=ASASTATSER, layout="dynamic")
        free = _user("layoutkey-4", permission=0, layout="dynamic")
        paid_html = _render(subscriber, payload)
        free_html = _render(free, payload)

        assert paid_html != free_html
        # Not compared with the anonymous page any more. It used to be, and that
        # assertion was the shared-cache bug written down as a requirement: a
        # signed-in free reader may export and an anonymous visitor may not, so
        # the two pages differ by the CSV export link and now key differently.
        # See TestCacheIsKeyedOnEntitlementToo below.
        assert free_html == _render(
            _user("layoutkey-4b", permission=0, layout="dynamic"), payload
        )

    def test_a_lapsed_subscriber_drops_back_to_the_default_page(self, payload):
        """Their saved choice survives; the page it resolves to does not.

        Compared against a reader of the same tier with no saved choice, not
        against the anonymous page. The anonymous page differs by the CSV export
        link now -- see TestCacheIsKeyedOnEntitlementToo -- and comparing with
        it would confuse "fell back to design 1" with "was treated as signed
        out", which are very different failures.
        """
        cache.clear()
        lapsed = _user("layoutkey-5", permission=INTRO, layout="dynamic-compact")
        plain = _user("layoutkey-5b", permission=INTRO, layout="")

        assert _render(lapsed, payload) == _render(plain, payload)
        assert lapsed.profile.preferred_layout == "dynamic-compact"

    def test_the_default_page_is_still_the_untouched_one(self, payload):
        """Design 1 is `frontend-before` plus the fold, and nothing else.

        Named here because the cache key is the mechanism that lets designs 2
        and 3 exist without a single line of theirs reaching this page.
        """
        cache.clear()
        html = _render(None, payload)

        assert "data-pid" not in html
        assert "js/pins.js" not in html
        assert "js/showmore.js" in html


@pytest.mark.django_db
class TestCachedPageIsSharedWithinOneLayout:
    """The constraint that keeps everything *else* per-reader off this page.

    Not a wish -- a demonstration of current behaviour. Anything besides the
    layout rendered into an address template is handed to the next reader on
    that layout, so the pins and the saved order live in `localStorage` and
    never reach the server.

    If these tests ever fail, the caching changed. That is good news, not a
    regression: check whether the view gained ``vary_on_cookie`` or moved to
    middleware-level caching, and if so more per-reader state can be rendered
    inline after all. Do not "fix" them by weakening the assertion.
    """

    def test_two_readers_on_one_layout_share_one_entry(self, payload):
        """The discriminating case: two *signed-in* readers, in order.

        Their sessions differ, their profiles differ, and the second is served
        the first's bytes. An anonymous-then-authenticated pair would pass here
        even with a leak present, which is why that pairing is not the test.
        """
        cache.clear()
        first = _user("layoutiso-2", INTRO)
        second = _user("layoutiso-3", INTRO)
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
            "the address page no longer shares a cache entry between readers on "
            "one layout -- see this class's docstring before changing anything"
        )

    def test_the_vary_header_does_not_key_the_entry(self, payload):
        """`Vary: Cookie` is on the response and plays no part in the lookup.

        This is the whole trap in one assertion. ``cache_page`` is a view
        decorator, so ``learn_cache_key`` runs before ``SessionMiddleware``
        appends ``Vary: Cookie`` -- the header is on the finished response, and
        reading it as evidence of per-reader keying is exactly the mistake this
        module exists to stop someone repeating. It is also why the layout is
        folded into the key prefix instead of being varied on.
        """
        cache.clear()
        first = _user("layoutvary-1", INTRO)
        second = _user("layoutvary-2", INTRO)
        p1, p2, p3, p4 = _render_patches(payload)
        with p1, p2, p3, p4:
            one = _client_for(first).get(f"/{ADDRESS}")
            two = _client_for(second).get(f"/{ADDRESS}")

        assert "Cookie" in one.headers.get("Vary", "")
        assert one.content == two.content, "Vary now keys the entry; see the docstring"

    def test_the_page_still_renders_entries(self, payload):
        """Guards the equality assertions from passing on an empty page.

        Two identical error pages would satisfy every comparison above.
        Counted on `.fitem` rather than `.position`: design 1 is the untouched
        old page and has no position component -- that belongs to the
        dynamic designs.
        """
        cache.clear()
        html = _render(None, payload)

        assert html.count('class="fitem') > 1

    def test_the_suite_runs_with_caching_switched_on(self):
        """Guards the guard.

        ``config.settings.development`` uses ``DummyCache``, under which every
        test in this class passes vacuously and the page looks perfectly
        isolated. ``frontend/pytest.ini`` pins the automated-test settings for
        this reason; a probe run outside that rootdir does not get them.
        """
        from django.conf import settings

        backend = settings.CACHES["default"]["BACKEND"]

        assert (
            "dummy" not in backend.lower()
        ), f"caching is disabled ({backend}); this module cannot detect anything"


@pytest.mark.django_db
class TestCacheIsKeyedOnEntitlementToo:
    """The layout is not the only per-reader thing this page renders.

    The header carries a Historic data link and a CSV export link, each behind
    its own gate. Keyed on the layout alone, an anonymous visitor and a
    signed-in reader shared one entry -- both resolve to `classic` -- so
    whichever asked first decided what everyone saw until it expired: an
    anonymous request hid the export link from every signed-in reader, and a
    signed-in one offered it to visitors who cannot use it.

    The reader who warms the entry goes *first* in each test on purpose. That
    is the only order in which the bug shows: with the wrong key the second
    reader inherits the first one's page, and an assertion that rendered them
    the other way round would pass against it.
    """

    def test_an_anonymous_page_is_not_served_to_a_signed_in_reader(self, payload):
        """The reported symptom, in the order that produces it."""
        cache.clear()
        anonymous = _render(None, payload)
        signed_in = _render(_user("entkey-1", permission=0), payload)

        assert "CSV export" not in anonymous
        assert "CSV export" in signed_in, (
            "the signed-in reader was served the anonymous page, so the export "
            "link they are entitled to is missing"
        )

    def test_a_signed_in_page_is_not_served_to_an_anonymous_visitor(self, payload):
        """The same leak in the other direction, which is the worse one.

        Offering an export link to somebody who cannot use it sends them to a
        page that turns them away.
        """
        cache.clear()
        signed_in = _render(_user("entkey-2", permission=0), payload)
        anonymous = _render(None, payload)

        assert "CSV export" in signed_in
        assert "CSV export" not in anonymous

    def test_readers_who_see_the_same_page_still_share_an_entry(self, payload):
        """The key must separate by entitlement, not by reader.

        Two readers with the same answers to both gates get one entry between
        them -- otherwise this is session-keyed caching with extra steps, which
        is what folding the gates into the prefix exists to avoid.
        """
        cache.clear()
        first = _user("entkey-3", permission=0)
        second = _user("entkey-4", permission=0)

        assert _render(first, payload) == _render(second, payload)

    def test_the_historic_gate_separates_entries_as_well(self, payload):
        """Two gates, both in the key.

        A free reader may export and may not open the widget; a subscriber may
        do both. They differ by the Historic data link alone, which is enough to
        need separate entries.
        """
        cache.clear()
        free = _render(_user("entkey-5", permission=0), payload)
        subscriber = _render(_user("entkey-6", permission=ASASTATSER), payload)

        assert "Historic data" not in free
        assert "Historic data" in subscriber
