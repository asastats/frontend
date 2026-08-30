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

#: Every page that carries the shared header block.
CONTENT_PAGES = [
    "about.html",
    "features.html",
    "tokenomics.html",
    "faq.html",
    "asm-privacy.html",
    "subscriptions.html",
    "export.html",
]

#: Those of them whose header introduces an `<article>` of prose.
#:
#: `export.html` is the one that does not, and it is not an oversight in the
#: template: it is a tool rather than a document -- a heading, the addresses
#: being exported, a progress indicator and a status panel. It carries the
#: header block and one `h1` like the rest, so it belongs in `CONTENT_PAGES`,
#: and it has no prose for a header to sit above, so the two ordering and
#: measure rules below have nothing to say about it.
#:
#: **Split into two lists rather than skipped at run time.** Both of those
#: tests used to call `pytest.skip` when a page had no article, which reported
#: two skips on every run and read as though something were unfinished. A
#: premise that does not apply to a page is a reason to leave the page out of
#: that test, not a reason to start it and give up. What `export.html` needs
#: instead is `test_core_page_header_shares_the_measure_of_its_container`.
PROSE_PAGES = [name for name in CONTENT_PAGES if name != "export.html"]

HEADER = re.compile(r'<header class="[^"]*\bmb-10\b[^"]*">')
H1 = re.compile(r"<h1\b")
ARTICLE = re.compile(r"<article\b")
MEASURE = re.compile(r"\bmax-w-(\w+)\b")


def _opening_tag(source, match):
    """Return the full opening tag `match` starts.

    :param source: the template's text
    :type source: str
    :param match: a match positioned at the tag's `<`
    :type match: :class:`re.Match`
    :return: str
    """
    return source[match.start() : source.index(">", match.start())]


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

    @pytest.mark.parametrize("name", PROSE_PAGES)
    def test_core_page_header_precedes_the_prose(self, name):
        """The header introduces the page, so it sits outside the article.

        Inside, its bottom margin stacked on the first heading's top margin and
        the `article > :first-child` reset stopped applying -- which is exactly
        what happened to Tokenomics and FAQ when this block was introduced.
        """
        source = _source(name)
        article = ARTICLE.search(source)

        assert article, f"{name} is listed as prose but has no <article>"
        assert HEADER.search(source).start() < article.start(), (
            f"{name} puts its page header inside the article"
        )

    @pytest.mark.parametrize("name", PROSE_PAGES)
    def test_core_page_header_shares_the_measure_of_its_prose(self, name):
        """A title centred over a different width reads as misaligned.

        This is what made the subtitles look wrong: `max-w-3xl` prose under a
        header spanning the full `max-w-6xl` of `main`.
        """
        source = _source(name)
        article = ARTICLE.search(source)

        assert article, f"{name} is listed as prose but has no <article>"
        header_width = MEASURE.search(HEADER.search(source).group(0))
        article_width = MEASURE.search(_opening_tag(source, article))

        assert header_width, f"{name} header sets no measure"
        assert article_width, f"{name} article sets no measure"
        assert header_width.group(1) == article_width.group(1), (
            f"{name} centres its header over max-w-{header_width.group(1)} but "
            f"its prose over max-w-{article_width.group(1)}"
        )

    def test_core_page_header_shares_the_measure_of_its_container(self):
        """The same rule as above, for the page that has no article.

        `export.html` centres a heading over a column of controls rather than
        over prose, so the width it has to agree with is the block that wraps
        it. Getting this wrong looks identical to the defect the article
        version guards -- a centred title on a different axis to what it
        introduces -- and nothing else would catch it, because the page is a
        tool and every other rule here is about documents.
        """
        source = _source("export.html")
        header = HEADER.search(source)

        assert header, "export.html has no page header block"
        header_width = MEASURE.search(header.group(0))
        assert header_width, "export.html header sets no measure"

        # The nearest measured wrapper above the header is what it is centred
        # against; on this page that is the outer column the controls sit in.
        wrappers = [
            match
            for match in MEASURE.finditer(source[: header.start()])
        ]
        assert wrappers, "export.html header has no measured container above it"
        assert header_width.group(1) == wrappers[-1].group(1), (
            f"export.html centres its header over max-w-{header_width.group(1)} "
            f"inside a max-w-{wrappers[-1].group(1)} column"
        )
