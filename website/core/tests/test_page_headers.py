"""The content pages share one page header, and it has to stay shared.

About, Features, Tokenomics, FAQ, the privacy policy, Subscriptions and Export
are the same kind of page: a title, a standfirst, then prose. They were not
built that way. Each carried its own arrangement, and once Tailwind's preflight
removed the browser's default heading sizes and margins, the differences turned
into defects that no test could see:

* the title rendered at body size, because nothing supplied a scale;
* the title and standfirst ran the full width of `main` while the prose under
  them was capped at `max-w-3xl`, so a centred subtitle was centred on a
  different axis to the text it introduced;
* nothing separated either from the first paragraph.

What is pinned here is the shape, not the styling: a single `<h1>` inside a
`<header>` that precedes the prose and shares its measure. The sizes live in
`@layer base` and in utilities, and `test_stylesheet_resets` covers those.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

#: The prose pages that share the header block.
CONTENT_PAGES = [
    "about.html",
    "features.html",
    "tokenomics.html",
    "faq.html",
    "asm-privacy.html",
    "subscriptions.html",
    "export.html",
]

HEADER = re.compile(r'<header class="[^"]*\bmb-10\b[^"]*">')
H1 = re.compile(r"<h1\b")
ARTICLE = re.compile(r"<article\b")


def _source(name):
    for directory in settings.TEMPLATES[0]["DIRS"]:
        path = Path(directory) / name
        if path.is_file():
            return path.read_text()
    raise AssertionError(f"{name} is not in any template directory")


class TestCorePageHeaders:
    """Testing class for the shared content-page header."""

    @pytest.mark.parametrize("name", CONTENT_PAGES)
    def test_core_page_header_exists(self, name):
        assert HEADER.search(_source(name)), (
            f"{name} has no page header block; its title will sit directly on "
            "the first paragraph"
        )

    @pytest.mark.parametrize("name", CONTENT_PAGES)
    def test_core_page_header_holds_exactly_one_h1(self, name):
        """One page, one top-level heading.

        Two h1s give a screen reader two candidates for what the page is, and
        none give it any.
        """
        source = _source(name)

        assert len(H1.findall(source)) == 1, f"{name} does not have exactly one h1"

    @pytest.mark.parametrize("name", CONTENT_PAGES)
    def test_core_page_header_precedes_the_prose(self, name):
        """The header introduces the page, so it sits outside the article.

        Inside, its bottom margin stacked on the first heading's top margin and
        the `article > :first-child` reset stopped applying -- which is exactly
        what happened to Tokenomics and FAQ when this block was introduced.
        """
        source = _source(name)
        article = ARTICLE.search(source)
        if not article:
            pytest.skip(f"{name} has no <article> to compare against")

        assert HEADER.search(source).start() < article.start(), (
            f"{name} puts its page header inside the article"
        )

    @pytest.mark.parametrize("name", CONTENT_PAGES)
    def test_core_page_header_shares_the_measure_of_its_prose(self, name):
        """A title centred over a different width reads as misaligned.

        This is what made the subtitles look wrong: `max-w-3xl` prose under a
        header spanning the full `max-w-6xl` of `main`.
        """
        source = _source(name)
        article = ARTICLE.search(source)
        if not article:
            pytest.skip(f"{name} has no <article> to compare against")

        header_tag = HEADER.search(source).group(0)
        article_tag = source[article.start(): source.index(">", article.start())]

        widths = re.compile(r"\bmax-w-(\w+)\b")
        header_width = widths.search(header_tag)
        article_width = widths.search(article_tag)

        assert header_width, f"{name} header sets no measure"
        assert article_width, f"{name} article sets no measure"
        assert header_width.group(1) == article_width.group(1), (
            f"{name} centres its header over max-w-{header_width.group(1)} but "
            f"its prose over max-w-{article_width.group(1)}"
        )
