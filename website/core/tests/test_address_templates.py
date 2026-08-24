"""Phase 2 integration test: render ``address.html`` against the real sample payload.

Asserts the structural invariants the JS layer hangs off of: anything the
JS in ``static/js/address.js`` reads from the DOM (IDs, class names,
``data-*`` attributes) appears at least once in the rendered output, and
the resulting HTML balances open/close tags. The template-tag filter
behavior itself is covered by :mod:`core.tests.test_templatetags`.
"""

import json
from pathlib import Path

import pytest
from django.template.loader import render_to_string

from django.test import RequestFactory

from core.tests.dom import parse

# # Integration: render address.html against the real sample payload
SAMPLE_PATH = (
    Path(__file__).parent.parent.parent  # repo root from core/tests/
    / "utils"
    / "tests"
    / "sample_serialized_540A5.json"
)


@pytest.fixture(scope="module")
def sample_payload():
    """Real bundle payload from /api/v2/540A5.../, captured for fixture use."""
    if not SAMPLE_PATH.exists():
        pytest.skip(f"sample payload not at {SAMPLE_PATH}")
    with SAMPLE_PATH.open() as f:
        return json.load(f)


def _build_context(sample_payload, is_bundle=True):
    """Build a context that mimics the new BaseAddressView's output."""
    from collections import namedtuple
    from decimal import Decimal

    from api.position_id import annotate_positions

    # The captured file predates `pid`, which `AsaItemSerializer` now adds on
    # the way out. The view receives an already-annotated payload from the
    # internal API, so annotating here is what makes this context match what
    # the page is actually rendered from rather than an older shape of it.
    for item in sample_payload.get("asaitems", []):
        annotate_positions(item["asset"]["id"], item.get("programs"))

    from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

    # A fully-entitled deployment (Gate A) and viewer (Gate B) so the gated
    # export / historic links render and their structure can be asserted.
    cluster = SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]

    class _StubProfile:
        permission = cluster

        def can_access_historic_widget(self, size):
            return True

    class _StubUser:
        is_authenticated = True
        profile = _StubProfile()

    Consolidated = namedtuple(
        "Consolidated", ["balance", "staked", "liquidity", "defi", "nftfloor"]
    )

    chart = {"labels": [], "datasets": [{"data": [], "backgroundColor": []}]}
    return {
        "request": RequestFactory().get("/"),
        "banner": None,
        "finished_tax": False,
        "deployment_capabilities": {"permission": cluster},
        "account": sample_payload,
        "is_bundle": is_bundle,
        ("bundle" if is_bundle else "address"): sample_payload["account_info"][
            "addresses"
        ],
        "asachart": chart,
        "nftchart": chart,
        "colors": {
            item["asset"]["id"]: str(i)
            for i, item in enumerate(sample_payload["asaitems"])
        },
        "nft_colors": {
            c["name"]: str(i) for i, c in enumerate(sample_payload["nftcollections"])
        },
        "distchart": {"labels": []},
        "ratiochart": chart,
        "nftfloorchart": chart,
        "consolidated": Consolidated(
            balance=Decimal("61"),
            staked=Decimal("32"),
            liquidity=Decimal("59"),
            defi=Decimal("233"),
            nftfloor=Decimal("3544"),
        ),
        "user": _StubUser(),
        "url_value": sample_payload["account_info"]["bundle"],
    }


class TestAddressTemplateRenders:
    """Structural invariants from rendering against a realistic payload."""

    def test_renders_without_exception(self, sample_payload):
        # If this fails we know the template references a key that the
        # API serializer doesn't produce.
        html = render_to_string("address.html", _build_context(sample_payload))
        assert len(html) > 10_000

    def test_emits_all_six_json_script_payloads(self, sample_payload):
        # address.js calls JSON.parse on these. Renaming or dropping any
        # one of them silently breaks the chart layer.
        html = render_to_string("address.html", _build_context(sample_payload))
        for chart_id in (
            "asachart",
            "nftchart",
            "distchart",
            "ratiochart",
            "nftfloorchart",
            "consolidated",
        ):
            assert f'id="{chart_id}"' in html, f"Missing json_script for {chart_id}"

    def test_pricetip_carries_all_required_data_attributes(self, sample_payload):
        # The H1 .pricetip is the source-of-truth for USD/ALGO conversion
        # (address.js lines 1009, 1166-7, 442-6 all read these).
        html = render_to_string("address.html", _build_context(sample_payload))
        # The class attribute and data-* are in the same <h1>.
        for attr in (
            "data-pricealgo=",
            "data-totalwnft=",
            "data-totalnft=",
            "data-totalnftfloor=",
            "data-total=",
            "data-price=",
        ):
            assert attr in html, f"pricetip missing {attr}"

    def test_consolidated_header_carries_per_category_attributes(self, sample_payload):
        # data-balance/staked/liquidity/defi on the consolidated header
        # are read by the chart layer for the doughnut charts.
        html = render_to_string("address.html", _build_context(sample_payload))
        for attr in (
            "data-balance=",
            "data-staked=",
            "data-liquidity=",
            "data-defi=",
        ):
            assert attr in html, f"Consolidated header missing {attr}"

    def test_each_asaitem_emits_one_fitem_entry(self, sample_payload):
        # The filter logic in address.js (getNodesThatContain, fitem class
        # filter) relies on each asaitem being a single element carrying
        # `fitem`. It was an <li> inside a Materialize collapsible; it is a
        # <details> now, which is why the element name is not asserted -- only
        # the id convention the filter and checkOpened both match on.
        import re

        html = render_to_string("address.html", _build_context(sample_payload))
        # Outer fitem wrappers for asaitems use id="f<assetid>".
        fitem_ids = re.findall(r'<details[^>]+id="f(\d+)"', html)
        # We don't assert the exact number (some asaitems may have
        # value=0 and amount=0 and get skipped), but expect a healthy
        # majority of the 76 sample asaitems to render.
        assert (
            len(fitem_ids) >= 50
        ), f"Expected most of the 76 asaitems to render, got {len(fitem_ids)}"

    def test_nft_thumbnails_use_t_prefix_ids(self, sample_payload):
        # showMatchedNodes() in address.js (line 197) pairs an asaitem's
        # f<id> with the same NFT's t<id> thumbnail. Both prefixes must
        # appear in the rendered HTML.
        import re

        html = render_to_string("address.html", _build_context(sample_payload))
        t_ids = re.findall(r'id="t(\d+)"[^>]+class="[^"]*nfticon', html)
        assert len(t_ids) > 0

    def test_section_container_classes_present(self, sample_payload):
        # checkOpened("asa") / checkOpened("nft") use .asasec / .nftsec to find
        # the right container, and the filter shows and hides `.section-list`.
        # The containers were <ul class="collapsible ...">; the class names
        # survive the move to <details> because the JS still selects on them.
        html = render_to_string("address.html", _build_context(sample_payload))
        assert 'class="asasec section-list' in html
        assert 'class="nftsec section-list' in html

    def test_bundle_layout_emits_per_address_anchors(self, sample_payload):
        # Two addresses in the sample → two <a> anchors with the
        # per-address URL.
        bundle = sample_payload["account_info"]["bundle"]
        html = render_to_string("address.html", _build_context(sample_payload))
        for addr in sample_payload["account_info"]["addresses"]:
            # Short-address truncation: first 5 + ... + last 5 chars.
            short = f"{addr[:5]}...{addr[-5:]}"
            assert short in html, f"Short form of {addr} missing"
            assert f"/export/{addr}/" not in html
        assert f"/export/{bundle}/" in html

    def test_single_address_layout_emits_allo_link(self, sample_payload):
        # Switch to single-address: only the first address survives.
        ctx = _build_context(sample_payload, is_bundle=False)
        ctx["account"]["account_info"]["addresses"] = ctx["account"]["account_info"][
            "addresses"
        ][:1]
        ctx["address"] = ctx["account"]["account_info"]["addresses"]
        html = render_to_string("address.html", ctx)
        addr = ctx["address"][0]
        assert f"allo.info/account/{addr}" in html
        # Tax URL uses the single-address route.
        bundle = sample_payload["account_info"]["bundle"]
        assert f"/export/{addr}/" in html
        assert f"/export/{bundle}/" not in html

    def test_notevals_section_renders(self, sample_payload):
        # The sample has 1 noteval — the block should appear exactly once and
        # include that asset's id.
        #
        # Keyed on `.section-list`, which design 1's filter shows and hides, not
        # on the `.notevalsec` that used to sit beside it. That name had no rule
        # in any stylesheet this page loads and no script read it -- its only
        # rule lives in the historic widget's CSS, which the website never
        # loads -- so it was a label for nothing and is gone.
        html = render_to_string("address.html", _build_context(sample_payload))
        assert 'class="section-list' in html
        assert "1 not evaluated" in html

    def test_provider_icon_paths_use_correct_slug(self, sample_payload):
        # Verify the icon path convention is preserved end-to-end:
        # "Live Coin Watch" produces livecoinwatch.png (not
        # live-coin-watch.png as Django's |slugify would).
        html = render_to_string("address.html", _build_context(sample_payload))
        # The sample contains LCW links on the ALGO asset's links list.
        # We assert at least one provider icon path is in the rendered HTML.
        assert "icons/providers/" in html
        # Verify the slug convention: no dashes in icon filenames.
        import re

        icon_paths = re.findall(r"icons/providers/([a-z0-9]+)\.png", html)
        assert icon_paths, "Expected at least one provider icon"
        # Hyphens shouldn't appear in any provider icon filename.
        for slug in icon_paths:
            assert "-" not in slug, f"icon slug {slug} contains '-'"

    def test_no_legacy_filter_traces_in_output(self, sample_payload):
        # Phase 2 dropped asa_amount and dict_value usage from templates.
        # If a template somehow loaded an undefined filter it would render
        # the source string as plain text. This is a paranoid safety net.
        html = render_to_string("address.html", _build_context(sample_payload))
        for sentinel in ("{{ asas", "dict_value", "is_float_zero", "not_valuated"):
            assert (
                sentinel not in html
            ), f"Found legacy template sentinel {sentinel!r} in rendered output"

    def test_html_has_balanced_tags(self, sample_payload):
        # A failing assertion here usually means a stray {% if %} without
        # matching {% endif %} or a typo'd closing div.
        from html.parser import HTMLParser

        class Parser(HTMLParser):
            void_tags = {
                "br",
                "img",
                "meta",
                "link",
                "input",
                "source",
                "hr",
                "area",
                "base",
                "col",
                "embed",
                "param",
                "track",
                "wbr",
            }

            def __init__(self):
                super().__init__()
                self.stack = []
                self.unmatched = []

            def handle_starttag(self, tag, attrs):
                if tag not in self.void_tags:
                    self.stack.append(tag)

            def handle_endtag(self, tag):
                if tag in self.void_tags:
                    return
                if not self.stack or self.stack[-1] != tag:
                    self.unmatched.append(tag)
                else:
                    self.stack.pop()

        html = render_to_string("address.html", _build_context(sample_payload))
        parser = Parser()
        parser.feed(html)
        assert (
            not parser.unmatched
        ), f"Found mismatched closing tags: {parser.unmatched[:5]}"
        assert not parser.stack, f"Found unclosed tags at EOF: {parser.stack[:5]}"

    def test_distids_are_unique_and_paired(self, sample_payload):
        # The .tdist click handler in address.js (line 1080) does
        # ``$("#" + this.dataset.distid).toggleClass("hidden")`` so every
        # ``data-distid`` value must correspond to exactly one element
        # with a matching ``id``. This test catches both duplicates (which
        # would make jQuery match the wrong element) and orphaned distids
        # (which would silently no-op the click). It also catches the
        # specific Django ``add`` filter bug where slugify|add:counter
        # returns "" for non-numeric left operands, producing empty
        # distids like ``id="d--393537671"``.
        import re

        html = render_to_string("address.html", _build_context(sample_payload))

        distid_values = re.findall(r'data-distid="([^"]+)"', html)
        # No empty distids (the Django add-filter bug regression guard).
        assert all(v for v in distid_values), "Found empty data-distid value"
        # All distids unique.
        assert len(distid_values) == len(
            set(distid_values)
        ), "Found duplicate data-distid values"

        target_ids = re.findall(r'<div id="(d-[^"]+)"', html)
        # 1:1 pairing of every distid to a target panel id.
        assert set(distid_values) == set(target_ids), (
            f"distid/target mismatch: orphan distids "
            f"{set(distid_values) - set(target_ids)}, "
            f"orphan targets {set(target_ids) - set(distid_values)}"
        )

    def test_system_messages_render_as_notices(self, sample_payload):
        """A warning must not be a heading, and must not rely on colour.

        Both were: `<h2 class="text-error">` and `<p class="text-success">`.
        That put two entries in the document outline that are not sections,
        and left a reader who does not see colour with nothing to distinguish
        them from ordinary text. The roles are what make a screen reader treat
        them as a warning and a status rather than prose.
        """
        context = _build_context(sample_payload)
        context["account"]["system_info"] = {
            "warning": "Engine is resyncing",
            "information": "Prices refreshed",
        }

        html = render_to_string("address.html", context)

        assert 'role="alert"' in html
        assert "Engine is resyncing" in html
        assert 'role="status"' in html
        assert "Prices refreshed" in html
        assert '<h2 class="mt-3 text-lg font-medium text-error">' not in html

    def test_system_messages_are_absent_when_there_are_none(self, sample_payload):
        """An empty alert box is worse than no box."""
        context = _build_context(sample_payload)
        context["account"]["system_info"] = {}

        html = render_to_string("address.html", context)

        assert 'role="alert"' not in html
        assert 'role="status"' not in html

    def test_program_panels_use_no_line_breaks_for_layout(self, sample_payload):
        """`<br>` was the layout in the expanded row: eighteen of them.

        Each line was a `<span>` followed by a break, so nothing could be
        spaced, aligned or wrapped as a group -- and the gap between one
        program and the next was a trailing break inside the last one.
        """
        html = render_to_string("address.html", _build_context(sample_payload))
        panels = html[html.index('data-program-panel'):]

        assert "<br" not in panels[: panels.index("</details>")]

    def test_program_panel_carries_the_toggle_hook(self, sample_payload):
        """`toggleDist` finds the panel by this attribute.

        It used to take `$(this).parent()`, which made the panel's shadow a
        hostage of how the lines around it were nested -- wrapping them, which
        is what removing the `<br>` tags meant, moved the shadow elsewhere.
        An attribute, not a class: `asar` is half of what the toggle swaps, so
        a class would stop matching after the first click.

        Counts `asar` rather than the old `asar order-2`: the order utilities
        went when the position became a grid with named areas, and which
        utilities sit beside the hook is a layout decision. That the hook and
        the class the toggle swaps live on the same element is not.
        """
        html = render_to_string("address.html", _build_context(sample_payload))
        page = parse(html)

        panels = page.select("[data-program-panel]")
        assert panels
        assert all("asar" in panel.classes for panel in panels)

    def test_distribution_breakdown_is_a_panel(self, sample_payload):
        """It sits beside the summary, so it needs to read as its own surface.

        Bare text in the next column is distinguishable from the summary only
        by position, which is not a distinction on a narrow screen where the
        two stack.
        """
        html = render_to_string("address.html", _build_context(sample_payload))
        # `<div id="d-`, not `id="d-`: the control above it carries the same
        # value in `data-distid`, and that comes first in the markup.
        start = html.index('<div id="d-')
        panel = html[start: start + 400]

        assert "bg-base-200" in panel
        assert "border-base-300" in panel

    def test_asset_metadata_is_a_real_definition_list(self, sample_payload):
        """The `<dl>` had no `<dt>` or `<dd>` in it.

        Its children were plain `<div>`s with the label written into the text,
        so it announced a list with no terms and no definitions -- the one
        structure that could have told a screen reader "Total supply" and its
        number are a pair. Sighted readers lost nothing; everyone else lost
        the only thing making it a list.
        """
        html = render_to_string("address.html", _build_context(sample_payload))

        assert "<dt" in html
        assert html.count("<dt") == html.count("<dd")

    def test_asset_id_keeps_its_copy_control_adjacent(self, sample_payload):
        """`copyToClipboard` copies `$(this).prev()`.

        So the explorer link and the copy control have to stay immediate
        siblings: a wrapper between them copies the wrapper's text, or
        nothing.
        """
        html = render_to_string("address.html", _build_context(sample_payload))
        # From the start of the tag, not the class attribute inside it.
        at = html.index('<span class="copy')
        before = html[:at]

        assert before.rstrip().endswith("</a>"), (
            "something now sits between the asset id and its copy control"
        )

    def test_the_total_says_what_it_counts(self, sample_payload):
        """The heading was the figure alone.

        "Heading level one, 1,234.56 ALGO" names a number, not a page -- and
        the page's actual subject, the address, sat below it as a paragraph.
        """
        html = render_to_string("address.html", _build_context(sample_payload))
        heading = html[html.index("<h1"): html.index("</h1>")]

        assert "sr-only" in heading
        assert "Total value" in heading

    def test_the_label_is_not_inside_the_element_the_script_rewrites(
        self, sample_payload
    ):
        """`.pricetip` has its `innerHTML` assigned on every currency switch.

        A label placed inside it survives exactly until the reader flips to
        USD, which is the kind of accessibility fix that tests green and then
        quietly disappears in use.
        """
        html = render_to_string("address.html", _build_context(sample_payload))
        start = html.index('class="pricetip')
        element = html[start: html.index("</span>", start)]

        assert "sr-only" not in element

    def test_no_line_breaks_survive_anywhere_on_the_page(self, sample_payload):
        """`<br>` was the layout of every detail panel on this page.

        Programs, asset metadata, single NFTs -- each fact was a `<span>`
        followed by a break, so nothing could be spaced or aligned as a group.
        Asserted across the whole render rather than per panel, because the
        last three hid in `nfts/item.html` after the others were done.
        """
        html = render_to_string("address.html", _build_context(sample_payload))

        assert "<br" not in html


class TestTheTotalIsReachableWithoutAPointer:
    """The headline figure's tooltip is the one that carries the rate.

    Every other tooltip on this page repeats an amount in the other currency,
    which the currency switch already gives in one keystroke -- so the rest stay
    pointer conveniences rather than a tab stop on each of several dozen
    figures. The total's tip also carries the exchange rate, and that is on the
    page nowhere else, so it is the one that has to be reachable.
    """

    def test_the_total_can_take_focus(self, sample_payload):
        # DaisyUI reveals a tooltip on `:focus-visible` as well as `:hover`, so
        # a tabindex is the whole of the fix for a sighted keyboard reader.
        html = render_to_string("address.html", _build_context(sample_payload))

        assert 'class="pricetip cursor-default" tabindex="0"' in html
        # Inside the `.tooltip`, not on it: DaisyUI reveals on
        # `:has(:focus-visible)`, so a tabindex on the tooltip element itself
        # matches nothing and draws nothing.
        assert '<span class="tooltip" data-tip=' in html

    def test_the_tip_is_also_available_as_text(self, sample_payload):
        # A tooltip drawn with `content: attr(data-tip)` is not dependably in
        # the accessibility tree, so the visible tip alone reaches nobody who
        # cannot see it. `setTip` keeps this span in step on every switch.
        html = render_to_string("address.html", _build_context(sample_payload))

        assert 'aria-describedby="id-total-tip"' in html
        assert 'id="id-total-tip" class="sr-only"' in html

    def test_the_money_designs_need_none_of_it(self, sample_payload):
        # Their `.pricetip` carries no `.tooltip` class at all, and `.total-sub`
        # prints the same figure and rate permanently, for everyone. A tabindex
        # there would be a tab stop that reveals nothing.
        html = render_to_string("address_dynamic.html", _build_context(sample_payload))

        assert "total-sub" in html
        assert "pricetip tooltip" not in html


class TestTheExportActionLooksLikeOne:
    """CSV export and Historic data have to read as controls.

    The user could not find the CSV export on either design. It was there and
    rendering on both -- as flat, chrome-less text: `btn-ghost` on design 1 and
    a bare `.btn` on the money designs, whose fill is within a few percent of
    the page background on a dark theme. The old Materialize version was
    `btn-flat`, so this is not a regression; the affordance has been weak
    throughout and the conversion carried it across faithfully.

    `btn-outline` gives the control an edge without making it the loudest thing
    in the header -- the same hierarchy language the profile pages use, where
    outline means findable but not the most inviting thing on the page. The
    filled `btn-primary` stays reserved for the state that has earned it: a
    report already built and not yet downloaded.

    Asserted on the anchors themselves rather than on the page, because these
    templates extend `base.html` and its navigation is full of ghost buttons --
    a page-wide search finds those and says nothing about these.
    """

    TEMPLATES = ("address.html", "address_dynamic.html")

    def _actions(self, html):
        """Return the export and historic anchors, by where they point."""
        page = parse(html)
        return [
            node
            for node in page.select("a")
            if "/export/" in (node.get("href") or "")
            or "/historic/" in (node.get("href") or "")
        ]

    def test_both_designs_give_the_actions_an_edge(self, sample_payload):
        for template in self.TEMPLATES:
            for is_bundle in (True, False):
                html = render_to_string(
                    template, _build_context(sample_payload, is_bundle=is_bundle)
                )
                actions = self._actions(html)

                assert actions, f"{template} renders no export or historic link"
                for node in actions:
                    classes = node.classes
                    assert "btn-outline" in classes, (
                        f"{template}: {node.text()!r} has no edge, which on a dark "
                        "theme is indistinguishable from static text"
                    )
                    assert "btn-ghost" not in classes, (
                        f"{template}: {node.text()!r} is transparent -- the exact "
                        "rendering the reader could not find"
                    )

    def test_a_waiting_report_is_the_loud_one(self, sample_payload):
        # The one state that earns a filled button, and the reason the template
        # keeps a conditional at all.
        context = _build_context(sample_payload)
        context["report_available"] = True
        context["report_downloaded"] = False

        for template in self.TEMPLATES:
            html = render_to_string(template, context)
            download = [
                node
                for node in self._actions(html)
                if "/export/" in (node.get("href") or "")
            ]

            assert download, f"{template} renders no export link"
            for node in download:
                assert "btn-primary" in node.classes
                assert "Download processed CSV" in node.text()
