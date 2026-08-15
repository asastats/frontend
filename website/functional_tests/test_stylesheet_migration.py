"""Guards the one invariant of the Materialize-to-DaisyUI migration.

**This module is scaffolding and is meant to be deleted.** It exists only while
the site has two base templates, and the day the last page leaves base.html it
has nothing left to say -- ``test_a_page_still_on_the_old_base_keeps_materialize``
will start failing precisely because the migration finished, which is the
signal to remove this file and collapse base_tw.html into base.html.

Why it needs to exist at all: Materialize and the DaisyUI build both define
``.btn``, ``.card``, ``.card-title``, ``.modal``, ``.badge``, ``.container``,
``.avatar``, ``.input``, ``.truncate``, ``.disabled`` and ``.fixed``. A page
that loaded both stylesheets would have whichever lost the cascade silently
deform. Nothing in the templates enforces the choice -- a stray
``{% extends 'base.html' %}`` breaks no unit test -- so it is asserted here
against the rendered page.

Tests for what those pages actually *do* live with their subject:
test_appearance, test_auth_pages, test_static_pages, test_subscriptions_page,
test_index_page and test_sitemap_html_page.
"""

from django.urls import reverse

from .base import FunctionalTest

#: Pages already moved onto base_tw.html, by URL name. Add to this as each
#: batch converts; the list is what makes the sweep meaningful.
CONVERTED = [
    "index",
    "about",
    "asm_privacy",
    "faq",
    "features",
    "sitemap",
    "tokenomics",
    "subscriptions",
    "disclaimer",
    "account_login",
    "account_signup",
    # base_home.html subtree (Batch C). Its other descendants -- account/base,
    # base_bundlename and socialaccount/base -- are held on
    # base_home_legacy.html until their batches convert, so they are asserted
    # on the OLD base below instead.
    "home",
    "profile",
    "profile_account",
    "profile_api",
    "profile_settings",
    "profile_addresses",
    "deactivate_profile",
]

#: Pages deliberately still on Materialize, via base_home_legacy.html. Each
#: moves up to CONVERTED as its batch lands, and the shim is deleted when this
#: list is empty.
STILL_LEGACY = ["account_email", "socialaccount_connections"]
#: bundlename_add is deliberately absent: SubscribeRedirection sends a viewer
#: without the tier to /subscriptions/, which IS converted, so the assertion
#: would be made against the wrong page. With the engine unreachable -- the
#: normal state in these tests -- deployment_capabilities returns a
#: zero-permission stub and every tier gate closes.


class StylesheetSplitTest(FunctionalTest):
    """Every page loads exactly one of the two stylesheets, never both."""

    # No backend mocking here, deliberately. functional_tests normally mocks the
    # engine (integration_tests/conftest.py takes the other route and starts it
    # on :8001), but every converted page must render with the engine
    # unreachable -- which is exactly the state it is in during these tests.
    # Adding a mock would hide a page that cannot stand on its own.

    def test_converted_pages_load_the_new_stylesheet_and_not_materialize(self):
        # The base_home pages redirect anonymous viewers to the login page,
        # which would make this assert the login page nine times over.
        self.create_cookie_and_go_to_index_page_tier(
            "sheets@example.com", permission=100
        )
        for name in CONVERTED:
            with self.subTest(page=name):
                state = self.visit(self.server_url + reverse(name))
                sheets = " ".join(state["sheets"])
                # templates/500.html carries inline CSS and links nothing, so
                # "no stylesheets" is how a server error looks from here.
                self.assertNotEqual(
                    state["title"],
                    "Internal server error",
                    f"{name} raised in the view{state['why']}",
                )
                self.assertTrue(
                    state["sheets"],
                    f"{name} linked no stylesheet at all{state['why']}",
                )
                self.assertIn(
                    "style.tw", sheets, f"{name} misses style.tw.css{state['why']}"
                )
                self.assertNotIn(
                    "materialize",
                    sheets,
                    f"{name} still loads Materialize{state['why']}",
                )
                # style.css is the Materialize-era sheet and goes with it.
                self.assertNotIn(
                    "style.min", sheets, f"{name} still loads style.min{state['why']}"
                )

    def test_pages_still_on_the_old_base_keep_materialize(self):
        """The other half of the invariant: the split is real, not accidental.

        These are held on base_home_legacy.html on purpose -- converting the
        base_home hub would otherwise have dragged them onto the DaisyUI
        stylesheet while they still carry Materialize markup. When this list
        empties, the migration is over: see the module docstring.
        """
        self.create_cookie_and_go_to_index_page_tier(
            "legacy@example.com", permission=100
        )
        for name in STILL_LEGACY:
            with self.subTest(page=name):
                state = self.visit(self.server_url + reverse(name))
                sheets = " ".join(state["sheets"])
                self.assertNotEqual(
                    state["title"],
                    "Internal server error",
                    f"{name} raised in the view{state['why']}",
                )
                self.assertIn(
                    "materialize", sheets, f"{name} lost Materialize{state['why']}"
                )
                self.assertNotIn(
                    "style.tw", sheets, f"{name} gained style.tw{state['why']}"
                )
