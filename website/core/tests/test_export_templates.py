"""The tax-report snippet's contact links are links a reader can see and click.

``snippets/taxfinished.html`` closes the CSV export flow by asking the reader to
report problems through GitHub, Discord, X or Reddit. For a long time it asked
with four empty ``<a>`` elements: the label was pushed off-screen by the sprite
rules' ``text-indent: -99999px`` and the icon came from a shared sprite sheet,
``img/social/social-c.png``, which is not in the tree. The image being absent
made them 32x32 boxes with nothing in them -- a paragraph inviting contact,
followed by four blank squares.

Nothing caught it because nothing rendered this snippet. The template had no
test of any kind; only the view's ``finished_tax`` context flag was covered, and
a flag says nothing about what reaches the page.

The rule this asserts: **every link here has visible text**. That is what makes
the difference between the old markup and the new one, and it is what an icon
font, a sprite or a background image can quietly take away again.
"""

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory

from core.tests.dom import parse

#: Where each link must go. The GitHub and Discord destinations are specific --
#: an issue form and one channel -- so a rewrite that redirects them at the
#: project's front page would be a regression, not a tidy-up.
EXPECTED = {
    "github.com/asastats/channel/issues": "an issue form, not the org page",
    "discord.com/channels/906917846754418770/1209176713485881384": (
        "the #tax-report channel, not the invite"
    ),
    "x.com/": "the project account",
    "reddit.com/r/": "the subreddit",
}


#: The Back link reverses `address`, whose pattern accepts exactly 58
#: characters -- a short placeholder fails the render with a NoReverseMatch
#: that reads as a missing route rather than a malformed argument.
ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"


@pytest.fixture
def rendered():
    """Return the snippet rendered with a finished report.

    :return: markup
    :rtype: str
    """
    return render_to_string(
        "snippets/taxfinished.html",
        {"bundle": None, "url_value": ADDRESS, "analysis_tax": None},
        request=RequestFactory().get(f"/export/{ADDRESS}/"),
    )


def test_export_taxfinished_contact_links_have_visible_text(rendered):
    """No link in the contact row is an empty element.

    An ``<a>`` with no text is only clickable when something else gives it a
    size, which here was a background image that no longer exists.
    """
    empty = [
        element.attrs.get("href", "")
        for element in parse(rendered).select("a")
        if not element.text().strip()
    ]

    assert not empty, f"contact links with no visible label: {empty}"


def test_export_taxfinished_keeps_its_four_destinations(rendered):
    """Each contact channel is still reachable, and still the specific one."""
    hrefs = [
        element.attrs.get("href", "") for element in parse(rendered).select("a")
    ]

    for fragment, why in EXPECTED.items():
        assert any(fragment in href for href in hrefs), (
            f"no link to {fragment} ({why}). Rendered hrefs: {hrefs}"
        )


def test_export_taxfinished_external_links_are_safe(rendered):
    """Every outbound link opens in a new tab without handing over the opener."""
    unsafe = [
        element.attrs.get("href")
        for element in parse(rendered).select("a")
        if element.attrs.get("href", "").startswith("http")
        and (
            element.attrs.get("target") != "_blank"
            or "noopener" not in element.attrs.get("rel", "")
        )
    ]

    assert not unsafe, f"external links missing target/rel: {unsafe}"


#: Tailwind's preflight resets headings to inherit their size and weight, so a
#: heading here is only a heading if it says so. These are the classes that make
#: the difference between a section title and a line of body text.
SIZING = ("text-xs", "text-sm", "text-base", "text-lg", "text-xl", "text-2xl")


def test_export_taxfinished_headings_are_styled_as_headings(rendered):
    """**A bare `<h4>` is body text on this site, not a heading.**

    Under Tailwind's preflight every heading is reset to inherit, so the two
    headings in this snippet rendered at body size and body weight and the page
    arrived as one undifferentiated column - which is what a reader reported.
    Nothing caught it because every other test here asks about links.

    Asserted on the class attribute rather than on computed style, because the
    stylesheet is not available to a template render. That is the weaker check,
    but it is the one that fails when someone writes `<h5>Something</h5>` again.
    """
    unstyled = [
        f"<{element.tag}> {element.text().strip()[:40]!r}"
        for element in parse(rendered).select("h1, h2, h3, h4, h5, h6")
        if not any(size in element.attrs.get("class", "") for size in SIZING)
    ]

    assert not unstyled, f"headings with no size class: {unstyled}"


def test_export_taxfinished_actions_sit_in_one_row(rendered):
    """Download, Refresh and Back are a button row, not a stack.

    Each was wrapped in its own `<div class="w-1/3">` with no flex parent, so
    they stacked vertically at a third of the width apiece. `w-1/3` on an action
    wrapper is the fingerprint of that layout and must not come back.
    """
    dom = parse(rendered)
    actions = [
        element
        for element in dom.select("#download, #refresh, #back")
        if element.attrs.get("id")
    ]
    assert len(actions) == 3, "expected download, refresh and back"

    thirds = [
        element.attrs.get("class", "")
        for element in dom.select("div")
        if "w-1/3" in element.attrs.get("class", "")
    ]
    assert not thirds, f"actions are still wrapped in thirds: {thirds}"


def test_export_taxfinished_agree_checkbox_is_styled(rendered):
    """The consent checkbox is the site's checkbox, not the browser's default.

    It carried no class at all, so it rendered as a raw native control in the
    middle of a DaisyUI page. The name is what the view reads, so both halves
    matter: it has to stay `agree`, and it has to look like the rest.
    """
    boxes = [
        element
        for element in parse(rendered).select("input")
        if element.attrs.get("type") == "checkbox"
    ]

    assert len(boxes) == 1, "expected exactly one consent checkbox"
    assert boxes[0].attrs.get("name") == "agree"
    assert "checkbox" in boxes[0].attrs.get("class", ""), (
        "the consent checkbox has no DaisyUI class"
    )


def test_export_taxfinished_agreement_is_a_list(rendered):
    """The three terms are an ordered list, not hand-numbered `<br><br>`.

    They were written as `1)`, `2)`, `3)` inside one paragraph, which is why
    they neither wrapped nor indented like a list. A reader skimming for the
    liability clause had no structure to skim.
    """
    items = parse(rendered).select("ol li")

    assert len(items) == 3, f"expected three agreement terms, got {len(items)}"
    assert not any(
        item.text().strip().startswith(("1)", "2)", "3)")) for item in items
    ), "the terms are still numbered by hand inside the list"
