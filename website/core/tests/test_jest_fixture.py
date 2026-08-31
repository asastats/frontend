"""The jest fixtures are the pages Django renders, not copies of them.

Two files here are loaded by jest suites and assigned to
``document.documentElement.innerHTML`` before the page's scripts are exercised:

* ``javascript_tests/index.html`` -- ``site.test.js`` and ``index.test.js``
* ``widgets/inhouse/historic/tests/javascript/index.html`` -- the widget's
  ``index.test.js``

Each is therefore a claim: *this is what the browser sees*. Nothing enforced
either claim, and both had stopped being true. They were snapshots of the
pre-DaisyUI pages, and the damage was quiet in three different ways.

**Dead CSS looked alive.** The old sprite footer survived only in these two
files, so every class in it answered a grep. A dozen stylesheet rules were kept
on the strength of markup that no page had rendered in months.

**Assertions passed against absent markup.** ``site.test.js`` looked up
``[role="alert"]`` and got the toast it had just created, because the old
fixture had no other alert. The real page has one -- ``#evm-app-error``, hidden,
and earlier in the document -- so two assertions were passing while checking an
element the code never touched.

**An accident became a specification.** The widget fixture had been captured
with the *Update* tab selected, and a test asserted that ``tupdate`` was the
open panel as though that were the page's initial state. It opens on ``tbars``.

**Why names and not bytes.** Neither page is byte-reproducible: the index H1
tagline is chosen at random per request and CSRF tokens are fresh each render.
Normalising those away would leave a comparison that breaks whenever anyone
edits a sentence. Classes and ids are the fixtures' real contract -- they are
what the suites select on and what the stylesheet is pruned against.

**To regenerate** after an intentional template change::

    REGENERATE_JEST_FIXTURE=1 python -m pytest core/tests/test_jest_fixture.py

Then re-run ``npx jest`` -- from ``website`` and from the widget's own directory,
which is a separate invocation -- and read the diff before committing it. A
fixture that changed for a reason nobody can name is what this module exists to
catch.

Both guards live here rather than beside their fixtures because the widget test
suite runs with its own rootdir, where ``core.templatetags.core_extras`` cannot
be imported and the render fails with an unrelated-looking
``InvalidTemplateLibrary``.
"""

import os
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory

WEBSITE = Path(__file__).parent.parent.parent

INDEX_FIXTURE = WEBSITE / "javascript_tests/index.html"
HISTORIC_FIXTURE = (
    WEBSITE / "widgets/inhouse/historic/tests/javascript/index.html"
)

#: A bundle is a 40-character hash, not an address: the `historic_reset` route
#: accepts only that width, so a 58-character address here fails the render with
#: a NoReverseMatch that names neither the width nor the reason.
BUNDLE = "540A5D8CEC896E073F9170AF0A962503E69147CF"

ADDRESSES = (
    "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU "
    "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
)

#: Written above the captured markup by the regeneration path below. Stripped
#: before comparison so the note is never mistaken for page content.
PROVENANCE = re.compile(r"\A\s*<!--.*?-->\s*", re.S)


#: An `id` attribute, and not the tail of a longer attribute name.
#:
#: This was `\bid="`, which is not the same thing: `-` is a non-word character,
#: so there is a word boundary between the dash and the `i` of
#: `data-wc-project-id="…"` and the pattern captured its value as though it were
#: an element id. That value comes from settings, so the guard compared one
#: deployment's WalletConnect project id against another's and failed on every
#: checkout but the one that generated the fixture -- which is the same shape of
#: fault as the manifests this repository stopped ignoring: a check that only
#: holds where it was written.
#:
#: The lookbehind rejects any preceding name character, so `data-user-id=`,
#: `data-pool-id=` and every other `*-id=` attribute are left alone while a bare
#: `id=` still matches.
ELEMENT_ID = re.compile(r'(?<![-\w])id="([^"]+)"')


def _names(html):
    """Return the class names and the element ids `html` contains.

    :param html: rendered markup
    :type html: str
    :return: tuple of two sets
    :rtype: tuple
    """
    classes = set()
    for value in re.findall(r'class="([^"]*)"', html):
        classes.update(value.split())

    return classes, set(ELEMENT_ID.findall(html))


def _compare(fixture_path, rendered):
    """Assert `fixture_path` and `rendered` agree, or regenerate the fixture.

    :param fixture_path: the jest fixture to check
    :type fixture_path: :class:`pathlib.Path`
    :param rendered: the page as Django renders it now
    :type rendered: str
    """
    if os.environ.get("REGENERATE_JEST_FIXTURE"):
        note = PROVENANCE.match(fixture_path.read_text())
        fixture_path.write_text((note.group(0) if note else "") + rendered)
        pytest.skip(f"regenerated {fixture_path.name}; re-run jest")

    fixture = PROVENANCE.sub("", fixture_path.read_text(), count=1)

    rendered_classes, rendered_ids = _names(rendered)
    fixture_classes, fixture_ids = _names(fixture)

    assert fixture_classes == rendered_classes, (
        f"{fixture_path.name} and the rendered page disagree about classes. "
        f"Only on the page: {sorted(rendered_classes - fixture_classes)}. Only "
        f"in the fixture (this is how dead CSS keeps looking used): "
        f"{sorted(fixture_classes - rendered_classes)}. Regenerate with "
        f"REGENERATE_JEST_FIXTURE=1 -- see this module's docstring."
    )
    assert fixture_ids == rendered_ids, (
        f"{fixture_path.name} and the rendered page disagree about ids. Only "
        f"on the page: {sorted(rendered_ids - fixture_ids)}. Only in the "
        f"fixture: {sorted(fixture_ids - rendered_ids)}."
    )


@pytest.mark.django_db
def test_jest_fixture_matches_the_rendered_index(client):
    """The index fixture still matches what ``/`` serves."""
    response = client.get("/")
    assert response.status_code == 200, response.status_code

    _compare(INDEX_FIXTURE, response.content.decode())


@pytest.mark.django_db
def test_jest_fixture_matches_the_rendered_historic_widget():
    """The historic widget's fixture still matches what its template renders.

    The view is behind a subscription gate, so the template is rendered with the
    context :class:`...historic.views.HistoricView` supplies rather than through
    the client. A request is passed so the context processors run: base.html's
    chrome comes from them, and that chrome is most of what went stale.
    """
    request = RequestFactory().get(f"/widgets/historic/{BUNDLE}")
    request.user = AnonymousUser()
    rendered = render_to_string(
        "historic/index.html",
        {
            "bundle": BUNDLE,
            "addresses": ADDRESSES,
            "website_name": settings.WEBSITE_NAME,
        },
        request=request,
    )

    _compare(HISTORIC_FIXTURE, rendered)
