"""Grid children need a grid.

Tailwind's ``col-span-*`` only means anything inside a ``grid`` container. On
its own it is not an error, does not warn, and does not show up in any log --
the element simply ignores it and falls into normal block flow, which reads as
"the right-hand column moved underneath the middle one".

That is what happened converting the profile pages off Materialize. ``col s12
m7`` and ``col s12 m5`` became ``md:col-span-7`` and ``md:col-span-5`` on five
templates, but on ``profile.html`` the wrapper declaring the twelve-column grid
was not carried across. Four pages looked right and the fifth stacked, with
identical-looking markup in all five.

The rule checked here is deliberately per-file rather than per-element: a
template that positions children in a grid should say which grid it means. Where
the container genuinely belongs to a parent template, name the file in
``GRID_FROM_PARENT`` and say which parent supplies it.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

#: Templates whose grid container is declared by the template they extend.
GRID_FROM_PARENT = {}

#: Matches `col-span-3`, `md:col-span-7`, `lg:col-span-2` and friends.
COL_SPAN = re.compile(r"[\w:]*\bcol-span-\w+")

#: Matches any grid-template declaration: `grid-cols-4`, `md:grid-cols-12`.
GRID_COLS = re.compile(r"[\w:]*\bgrid-cols-\w+")


def _templates_using_col_span():
    """Yield (name, text) for every template that positions grid children."""
    for directory in settings.TEMPLATES[0]["DIRS"]:
        root = Path(directory)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.html")):
            text = path.read_text(errors="ignore")
            if COL_SPAN.search(text):
                yield path.relative_to(root).as_posix(), text


USERS = list(_templates_using_col_span())


class TestGridChildrenHaveAGrid:
    """Testing class for grid positioning classes across templates."""

    def test_core_col_span_users_are_discoverable(self):
        """Guard the guard: an empty list would make this suite vacuous."""
        assert USERS, (
            "no template uses col-span-* -- either the layout no longer uses "
            "CSS grid, in which case delete this module, or discovery is "
            "looking in the wrong place"
        )

    @pytest.mark.parametrize("name,text", USERS, ids=[n for n, _ in USERS])
    def test_core_template_declares_the_grid_it_spans(self, name, text):
        """`name` must declare a grid, or say which parent declares it.

        :param name: template path relative to the templates directory
        :type name: str
        :param text: the template source
        :type text: str
        """
        if name in GRID_FROM_PARENT:
            return
        assert GRID_COLS.search(text), (
            f"{name} uses {sorted(set(COL_SPAN.findall(text)))} but declares no "
            "grid-cols-* container. Outside a grid those classes do nothing at "
            "all: the columns stack instead of sitting side by side, and "
            "nothing anywhere reports it. Add the wrapper, or list the file in "
            "GRID_FROM_PARENT naming the parent that supplies the grid."
        )
