"""Django's `{# #}` is a single-line comment, and nothing enforces that.

An unclosed one does not raise, does not warn, and does not fail to render. It
renders **as text**, in the page, to the reader -- which is how three of them
shipped into the swap panel and turned "YOU PAY" into "YOU PAY {# THE COMPUTED
LEG'S WORTH IN USDC. ONE PER LEG BECAUSE `POSITIONAMOUNTFIELD` MOVES ...", in
uppercase, because the caption row is `text-transform: uppercase`.

The multi-line form is `{% comment %}`; `{# #}` may also span lines *if each
line closes its own*, which is a common and correct idiom here. So the rule is
not "no `{#` without `#}` in the file" but "no `{#` without `#}` on its line".

This is the cheapest possible check for a defect class that is invisible to
every other kind of test: the template compiles, the view returns 200, and the
only symptom is prose where a label should be.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

#: `{#` that never closes before the end of its own line.
UNCLOSED = re.compile(r"\{#(?![^\n]*#\})")


def _templates():
    """Return every template shipped by this project.

    Both the shared directories and the widgets' own, because a widget's
    partial renders into the same page and fails the same way.
    """
    roots = [Path(one) for one in settings.TEMPLATES[0]["DIRS"]]
    roots.append(Path(settings.BASE_DIR) / "widgets")
    seen = []
    for root in roots:
        if not root.is_dir():
            continue

        seen.extend(
            path
            for path in root.rglob("*.html")
            if "node_modules" not in path.parts and "coverage" not in path.parts
        )
    return sorted(set(seen))


def test_core_templates_are_discovered():
    """A search that finds nothing passes every assertion below it."""
    assert len(_templates()) > 50


@pytest.mark.parametrize("path", _templates(), ids=lambda p: p.name)
def test_core_template_has_no_unclosed_comment(path):
    source = path.read_text()
    offenders = [
        source[: match.start()].count("\n") + 1
        for match in UNCLOSED.finditer(source)
    ]

    assert not offenders, (
        f"{path}: `{{#` on line(s) {offenders} does not close on its own line, "
        "so Django renders it as text. Use `{% comment %}` for a multi-line "
        "comment, or close each line's own `{# #}`."
    )
