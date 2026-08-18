"""Every template in the project must compile.

This is deliberately the cheapest possible test: it loads each template through
Django's own loader, which parses it and resolves its tags and filters, but
renders nothing. No browser, no database, no fixtures.

It exists because template syntax errors are otherwise found the slow way. Two
real ones during the Materialize-to-DaisyUI migration would have been caught
here in milliseconds instead:

* a ``{% comment %}`` block placed above ``{% extends %}``, which is invalid --
  ``{% extends %}`` must be the first tag in a template -- and took down every
  page in that inheritance chain;
* a search-and-replace that reached inside a class attribute and turned
  ``{% if row.is_primary %}`` into ``{% if .is_primary %}``.

Both surfaced as a wall of failures in the functional suite, pointing at the
pages rather than at the cause.
"""

from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse

#: Directories under templates/ that hold things the loader should not compile.
EXCLUDED_DIRS = {"jsonld"}

#: Suffixes that are data, not templates.
EXCLUDED_SUFFIXES = {".jsonld", ".txt"}


def _template_names():
    """Yield every template path, relative to its template directory."""
    for directory in settings.TEMPLATES[0]["DIRS"]:
        root = Path(directory)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.html")):
            relative = path.relative_to(root)
            if EXCLUDED_DIRS & set(relative.parts):
                continue
            if path.suffix in EXCLUDED_SUFFIXES:
                continue
            yield relative.as_posix()


TEMPLATE_NAMES = list(_template_names())


class TestEveryTemplateCompiles:
    """Testing class for template syntax across the whole project."""

    def test_core_templates_directory_is_discoverable(self):
        """Guard the guard: an empty list would make this suite vacuous."""
        assert len(TEMPLATE_NAMES) > 50, (
            "found almost no templates -- the discovery above is probably "
            f"looking in the wrong place: {TEMPLATE_NAMES[:5]}"
        )

    @pytest.mark.parametrize("name", TEMPLATE_NAMES)
    def test_core_template_compiles(self, name):
        """Load `name` through the configured loaders.

        :param name: template path relative to the templates directory
        :type name: str
        """
        get_template(name)


class FooterLinksTest(TestCase):
    """The footer is the site's full map, so what is missing from it is lost.

    The header carries a short list that changes with the reader; everything
    else is reachable only from here. A page that exists and is linked nowhere
    is a page nobody finds.
    """

    def setUp(self):
        self.url = reverse("about")

    def _sign_in(self):
        user = get_user_model().objects.create_user(
            username="footer@example.com", email="footer@example.com", password="x"
        )
        self.client.force_login(user)
        return user

    def _footer(self, response):
        html = response.content.decode()
        return html[html.index("<footer") : html.index("</footer>")]

    def test_core_footer_offers_the_sitemap(self):
        footer = self._footer(self.client.get(self.url))

        self.assertIn(reverse("sitemap"), footer)

    def test_core_footer_offers_both_app_stores(self):
        """They moved from a bottom strip into Product, where they belong."""
        footer = self._footer(self.client.get(self.url))

        self.assertIn("apps.apple.com", footer)
        self.assertIn("play.google.com", footer)

    def test_core_footer_offers_login_to_a_signed_out_reader(self):
        footer = self._footer(self.client.get(self.url))

        self.assertIn("#modalLogin", footer)

    def test_core_footer_offers_no_login_to_a_signed_in_reader(self):
        """A control that cannot do anything is worse than none."""
        self._sign_in()

        footer = self._footer(self.client.get(self.url))

        self.assertNotIn("#modalLogin", footer)

    def test_core_footer_offers_home_only_where_it_works(self):
        """`home` redirects a signed-out visitor, so offering it bounces them.

        It shared a slot with Log in until that moved to the About column; this
        is what stops the move from leaving a dead link behind.
        """
        anonymous = self._footer(self.client.get(self.url))
        self.assertNotIn(reverse("home"), anonymous)

        self._sign_in()
        self.assertIn(reverse("home"), self._footer(self.client.get(self.url)))
