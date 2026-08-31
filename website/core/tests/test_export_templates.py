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
