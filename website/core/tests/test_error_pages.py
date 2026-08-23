"""The error pages stand alone, and still look like the site.

404, 500 and 500r are the one place the built stylesheet cannot be relied on: a
500 is often exactly the moment `style.tw.css` is missing, stale or unreachable.
So these three link nothing and inherit nothing -- no `{% extends %}`, no
`<link rel="stylesheet">` -- and that independence is the point of them.

What was wrong is that they also looked nothing like the site: fixed light
colours on an implicit white background, `display: table` centring, `<br>` for
vertical rhythm, a paragraph pinned to 400px. A reader who hit one from a
dark-themed site got a flash of white and a page from another decade.

They carry their own inline palette now, copied from the `asastats` and
`asastats-dark` themes and switched on `prefers-color-scheme` -- the closest
honest answer, since which of the 57 themes a reader picked lives in storage an
error page has no business reaching for.

**The assertion worth having is the last one.** A copied palette drifts, and
nothing else in the codebase would notice: the error pages render fine with
stale colours, and no test that reads `input.css` reads these. So the colours
are compared against the themes they were copied from, by value.
"""

import re

from pathlib import Path

import pytest
from django.template.loader import render_to_string

#: The standalone pages. `500r` is served while Redis warms and is the only one
#: that loads anything external -- `reload-delayed.js`, which does the refresh.
ERROR_PAGES = ("404.html", "500.html", "500r.html")

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"
INPUT_CSS = Path(__file__).resolve().parents[2] / "static" / "css" / "input.css"

#: Copied into `snippets/error_style.html`, and the theme each came from.
#: `--color-primary` is deliberately absent: both themes use the same accent,
#: so it would not tell the two apart if one changed.
COPIED = {
    "asastats": {
        "--bg": "--color-base-100",
        "--raised": "--color-base-200",
        "--edge": "--color-base-300",
        "--ink": "--color-base-content",
    },
    "asastats-dark": {
        "--bg": "--color-base-100",
        "--raised": "--color-base-200",
        "--edge": "--color-base-300",
        "--ink": "--color-base-content",
    },
}


def _rendered(name):
    """Return one error page as it is served."""
    return render_to_string(name)


def _theme_tokens(theme):
    """Return one theme's declared colours from ``input.css``.

    :param theme: the `name:` of a `@plugin "daisyui/theme"` block
    :type theme: str
    :return: dict of token name to colour
    """
    css = INPUT_CSS.read_text()
    start = css.index(f'name: "{theme}";')
    end = css.index("}", start)
    return dict(re.findall(r"(--color-[\w-]+):\s*([^;]+);", css[start:end]))


@pytest.mark.parametrize("name", ERROR_PAGES)
def test_core_error_page_links_no_stylesheet(name):
    """The whole reason these are hand-written documents.

    A `<link>` here would make the page that reports a broken site depend on
    the site being unbroken.
    """
    html = _rendered(name)

    assert "<link" not in html, f"{name} links an external stylesheet"
    assert "{% extends" not in html and "style.tw.css" not in html


@pytest.mark.parametrize("name", ERROR_PAGES)
def test_core_error_page_carries_its_own_style(name):
    """Independent, but not unstyled -- which is what it was before."""
    html = _rendered(name)

    assert "<style>" in html
    assert "prefers-color-scheme: dark" in html, (
        f"{name} has one palette, so a reader on a dark site gets a white flash"
    )


@pytest.mark.parametrize("name", ERROR_PAGES)
def test_core_error_page_uses_no_layout_breaks(name):
    """`<br><br>` was the vertical rhythm on all three."""
    assert not re.search(r"<br\s*/?>", _rendered(name), re.IGNORECASE)


@pytest.mark.parametrize("name", ERROR_PAGES)
def test_core_error_page_is_big_enough_for_internet_explorer(name):
    """Under 512 bytes and IE substitutes its own error page.

    Long obsolete, and kept because the cost is a comment and the failure it
    prevents is invisible: the page is simply replaced by the browser's.
    """
    assert len(_rendered(name).encode()) > 512


def test_core_error_page_offers_a_way_out():
    """A dead end is worse than an error.

    Not asserted for `500r`, which reloads itself -- a link away from a page
    that is about to refresh would be a race the reader loses.
    """
    for name in ("404.html", "500.html"):
        assert 'class="action"' in _rendered(name), f"{name} offers no way back"


def test_core_error_page_reload_script_survives():
    """`500r` refreshes itself; without this the reader has to notice and retry."""
    assert "reload-delayed.js" in _rendered("500r.html")


@pytest.mark.parametrize("theme", sorted(COPIED))
def test_core_error_page_palette_matches_the_theme_it_copied(theme):
    """The one that earns its place.

    These colours are a *copy* of the theme's, because the page cannot load the
    stylesheet that holds the original. Nothing else would notice them drifting
    -- the pages render perfectly well in the wrong colours -- so the copy is
    compared with its source by value.
    """
    style = (TEMPLATE_DIR / "snippets" / "error_style.html").read_text()
    tokens = _theme_tokens(theme)
    # The dark palette lives inside the media query; the light one before it.
    dark_at = style.index("prefers-color-scheme: dark")
    block = style[dark_at:] if theme.endswith("-dark") else style[:dark_at]

    for local, source in COPIED[theme].items():
        expected = tokens[source].split()[0].strip()
        assert f"{local}: {expected};" in block, (
            f"{theme}: the error pages' {local} is not {source} ({expected}). "
            "They are a copy of the theme and have drifted from it."
        )
