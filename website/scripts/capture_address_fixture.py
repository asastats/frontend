#!/usr/bin/env python
"""Re-capture the address-page DOM fixture used by address.test.js.

    python scripts/capture_address_fixture.py

The jest suite for `static/js/address.js` needs a DOM to bind to, and that DOM
has to be the one the site actually serves: every selector in address.js is a
contract with `address.html` and its snippets, and a hand-written approximation
of the page can drift from it without a single test failing.

Which is what happened. `javascript_tests/address.html` was a captured render
that fell 3,000 lines behind the template, and nothing noticed because no test
read it -- the suite built its own inline fixture instead, with hooks
(`#if1`, `#other`, `#distbox`) the real page never emitted.

Rendered against the same trimmed sample payload the template tests use, so
this file and `core/tests/test_address_templates.py` describe one page. Trimmed
because the untrimmed payload renders 831KB, and jsdom parses the fixture once
per test.
"""

import json
import os
import re
import pathlib
import sys

import django

HERE = pathlib.Path(__file__).resolve().parent
WEBSITE = HERE.parent

#: Kept small enough to parse quickly, complete enough to carry every hook:
#: assets with programs and distributions, collections with thumbnails, and an
#: unevaluated entry.
ASA_ITEMS = 3
COLLECTIONS = 2
NFTS_PER_COLLECTION = 3
NOTEVALS = 2

BANNER = """<!--
  Snapshot of a rendered address page, used as the DOM fixture for
  address.test.js.

  CAPTURED OUTPUT, NOT HAND-WRITTEN MARKUP. Regenerate it rather than editing
  it: `scripts/capture_address_fixture.py` renders `address.html` against the
  same trimmed sample payload the template tests use. Editing it by hand makes
  the tests pass against a page the site does not serve, which is exactly what
  happened before -- this file sat 3,000 lines behind the template while every
  test went on passing, because nothing read it at all.

  Trimmed to three assets, two collections and one unevaluated entry: enough
  to carry every hook address.js binds to, without loading a whole portfolio
  into jsdom on each test.
-->
"""


def main():
    sys.path.insert(0, str(WEBSITE))
    os.chdir(WEBSITE)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.automated_tests")
    django.setup()

    from django.template.loader import render_to_string
    from django.test.utils import setup_test_environment

    setup_test_environment()

    # The context builder lives with the template tests; importing it is what
    # keeps the fixture and those tests describing the same page.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "test_address_templates", WEBSITE / "core" / "tests" / "test_address_templates.py"
    )
    templates_test = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(templates_test)

    payload = json.loads(pathlib.Path(templates_test.SAMPLE_PATH).read_text())
    trimmed = dict(payload)
    trimmed["asaitems"] = payload["asaitems"][:ASA_ITEMS]
    trimmed["nftcollections"] = [
        {**collection, "nfts": collection["nfts"][:NFTS_PER_COLLECTION]}
        for collection in payload["nftcollections"][:COLLECTIONS]
    ]
    trimmed["notevals"] = payload.get("notevals", [])[:NOTEVALS]

    context = templates_test._build_context(trimmed)

    # Real charts, computed the way the view computes them. The template tests
    # stub these -- charts are the view's work, not the template's -- but a
    # fixture with empty payloads cannot exercise a single line of the chart
    # code in address.js, which is most of it.
    from utils.charts import (
        prepare_base_charts_from_serialized_data,
        prepare_consolidated_charts_from_serialized_data,
    )

    (
        context["asachart"],
        context["nftchart"],
        context["colors"],
        context["nft_colors"],
    ) = prepare_base_charts_from_serialized_data(trimmed)
    (
        context["distchart"],
        context["ratiochart"],
        context["nftfloorchart"],
        context["consolidated"],
    ) = prepare_consolidated_charts_from_serialized_data(trimmed, context["nft_colors"])

    # `render_to_string` without a request runs no context processors, so the
    # fold sizes the page publishes as `data-initial` would come out empty and
    # `showmore.js` would fall back to revealing whole sections -- which is not
    # what any reader sees. Named here rather than left blank because the
    # fixture is the DOM the jest suites reason about.
    from django.conf import settings

    context.setdefault("ADDRESS_INITIAL_ASSETS", settings.ADDRESS_INITIAL_ASSETS)
    context.setdefault(
        "ADDRESS_INITIAL_COLLECTIONS", settings.ADDRESS_INITIAL_COLLECTIONS
    )

    html = render_to_string("address.html", context)

    # Only what the page itself renders. The surrounding `base.html` chrome is
    # a liability in jsdom: its <script> tags execute, its stylesheet <link>s
    # fetch, and none of it is what address.js binds to. The charts' payloads
    # survive because they are `type="application/json"` and inert.
    main = re.search(r"<main[^>]*>(.*)</main>", html, re.DOTALL)
    if not main:
        raise SystemExit("no <main> in the rendered page -- has base.html changed?")
    body = main.group(1)
    body = re.sub(
        r'<script(?![^>]*type="application/json")[^>]*>.*?</script>',
        "",
        body,
        flags=re.DOTALL,
    )
    html = BANNER + body.strip() + "\n"

    out = WEBSITE / "javascript_tests" / "address.html"
    out.write_text(html)
    print(f"wrote {out.relative_to(WEBSITE)} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
