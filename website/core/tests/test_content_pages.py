"""The content pages use real structure, not bullets and line breaks.

These six pages had their Tailwind wrappers -- the centred column, `space-y-4`,
the muted body colour -- around content still written the way Materialize left
it. Every list was a run of ``&#8226;`` characters and ``<br>`` tags inside one
``<p>``, and the vertical rhythm was more ``<br>`` inside containers that
already space their children. 163 breaks and 59 bullet characters across the
six.

That is not a styling complaint. A list built from bullet characters is one
paragraph as far as the document is concerned, so a screen reader announces a
wall of prose where a sighted reader sees five items, and says nothing about how
many there are or where each begins. The same goes for the numbered steps on the
subscriptions page, whose "1." and "2." were literal text: nothing announced a
sequence, and nothing renumbered it if a step were inserted.

Two of the pages were also malformed in ways the browser was quietly repairing:
an ``about`` paragraph was never closed and ran into a pull quote, and another
section's bullets sat directly inside a ``<div>`` with no paragraph at all.

**What is asserted and what is not.** Not "no ``<br>`` anywhere" -- a line break
is legitimate inside an address or a line of verse, and a rule that forbids it
outright is a rule someone will have to fight. What is asserted is the shape
this pass removed: a break used to end a list line, a break used as a spacer
between blocks, and a bullet character standing in for a list. Those have no
honest use on these pages.
"""

import re

from pathlib import Path

import pytest

#: The content pages this covers. Named rather than globbed: the address page
#: and the profile pages are applications, not prose, and hold their own rules.
TEMPLATES = (
    "about.html",
    "asm-privacy.html",
    "faq.html",
    "features.html",
    "subscriptions.html",
    "tokenomics.html",
)

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"

#: Characters these pages used to start a list line with.
LIST_MARKERS = ("&#8226;", "•")

#: A Django template comment. Stripped first: these templates explain the very
#: markup they no longer contain, and a search over the raw text finds the
#: explanation and reports the page as unconverted.
COMMENT = re.compile(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", re.DOTALL)

BREAK = re.compile(r"<br\s*/?>", re.IGNORECASE)

#: An opening paragraph tag, with or without attributes -- counting `"<p>"`
#: alone misses every `<p class="mt-2">` and reports a balanced page as broken.
P_OPEN = re.compile(r"<p(?:\s[^>]*)?>", re.IGNORECASE)
P_CLOSE = re.compile(r"</p>", re.IGNORECASE)


def _markup(name):
    """Return one template's markup with its comments removed."""
    return COMMENT.sub("", (TEMPLATE_DIR / name).read_text())


@pytest.mark.parametrize("name", TEMPLATES)
def test_core_content_page_has_no_layout_breaks(name):
    """`<br>` as spacing or as a list terminator, which is all it was used for.

    Every occurrence on these pages was one of those two, so the check is a
    count rather than a shape: if one comes back it is worth a look, and the
    docstring above says when a break would be legitimate.
    """
    found = BREAK.findall(_markup(name))

    assert not found, (
        f"{name} uses {len(found)} <br>. On these pages a break was only ever "
        "spacing, which the container already provides, or the end of a list "
        "line, which belongs in <li>."
    )


@pytest.mark.parametrize("name", TEMPLATES)
def test_core_content_page_has_no_bullet_characters(name):
    """A bullet character is a list drawn as prose.

    The document sees one paragraph, so nothing announces how many items there
    are or where one ends -- which is the whole reason `<ul>` exists.
    """
    markup = _markup(name)
    found = [marker for marker in LIST_MARKERS if marker in markup]

    assert not found, (
        f"{name} draws a list with {found} instead of marking one up. "
        "Use <ul><li>, or <ol><li> when the order is part of the meaning."
    )


@pytest.mark.parametrize("name", TEMPLATES)
def test_core_content_page_paragraphs_are_closed(name):
    """`about.html` had one that was not, and it swallowed a pull quote.

    The browser repairs this and the page looks right, so nothing catches it by
    eye -- but the quote ended up inside the paragraph above it, and every rule
    written for one applied to the other.
    """
    markup = _markup(name)
    opened = len(P_OPEN.findall(markup))
    closed = len(P_CLOSE.findall(markup))

    assert opened == closed, (
        f"{name} has {opened} opening <p> and {closed} closing </p>. "
        "An unclosed paragraph absorbs whatever follows it."
    )


def test_core_content_pages_actually_carry_lists():
    """Guard the guard.

    Every assertion above is satisfied by deleting the content, so this pins
    that the lists are still there. The count is deliberately loose -- it says
    the pass happened, not how the pages are written.
    """
    total = sum(_markup(name).count("<li>") for name in TEMPLATES)

    assert total > 40, f"only {total} list items across the content pages"
