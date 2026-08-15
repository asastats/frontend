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
from django.template.loader import get_template

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
