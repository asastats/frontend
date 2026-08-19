"""The interface between ``address.html`` and the scripts that read it.

Every assertion here corresponds to a real binding in ``static/js/address.js``
or ``static/js/site.js``, and each one's docstring says which. ``SELECTOR_CONTRACT.md``
is the longer prose companion -- read it before renaming anything on that page --
but it is documentation, not a fixture: nothing here reads it, and moving or
renaming it must never fail a test. The reasoning that stops a rename lives in
the docstrings below, because that is what prints when one of these fails.

They exist
because the address page has twice shipped a silent regression of exactly this
shape: markup moved, nothing threw, no test failed, and behaviour was quietly
gone -- the jest fixture drifting 3,000 lines behind its template, and the
in-place controls losing every cue but ``cursor: pointer`` in the DaisyUI
conversion.

Deliberately not a snapshot test. A snapshot fails on whitespace and gets
regenerated without being read, which is how the fixture drifted in the first
place. Each test below names one behaviour and says what breaks without it, so
a failure is a decision to make rather than a diff to accept.

The multi-layout redesign moves far more markup than either earlier change did.
When a layout genuinely needs to move something asserted here, change the
contract, this test and the JavaScript in the same commit.
"""

import pytest
from django.template.loader import render_to_string

from core.tests.dom import parse

from core.tests.test_address_templates import _build_context, sample_payload  # noqa: F401


@pytest.fixture(scope="module")
def page(sample_payload):  # noqa: F811
    """The address page rendered against the real bundle payload."""
    return parse(render_to_string("address.html", _build_context(sample_payload)))


class TestPageSingletons:
    """Elements the scripts address by id, or by taking the first match."""

    def test_pricetip_is_the_only_one_on_the_page(self, page):
        """`setCurrency` reads `$(".pricetip")[0]` -- the first match wins.

        A second one renders as a total that never converts, with nothing to
        say why. If a layout ever needs two, the script has to loop.
        """
        tips = page.select(".pricetip")

        assert len(tips) == 1, f"{len(tips)} .pricetip elements; the script reads one"

    @pytest.mark.parametrize(
        "attribute",
        [
            "data-price",
            "data-pricealgo",
            "data-total",
            "data-totalwnft",
            "data-totalnft",
        ],
    )
    def test_pricetip_carries_the_figures_the_switch_needs(self, page, attribute):
        """Currency conversion and "total without NFTs" both read these.

        They are the only source for either number: the rendered text is
        replaced wholesale, so nothing can be recovered from it afterwards.
        """
        tip = page.select_one(".pricetip")

        assert tip is not None, ".pricetip is gone; the header total cannot convert"
        assert tip.has_attr(attribute), f".pricetip has no {attribute}"

    def test_pricetip_holds_no_markup_of_its_own(self, page):
        """Because `setCurrency` assigns `innerHTML` over it.

        Any child element is destroyed the first time a reader switches to USD.
        This is why the screen-reader label for the total sits outside it, and
        the reason that label was moved there in the first place.
        """
        assert not page.select_one(".pricetip").has_element_children()

    @pytest.mark.parametrize(
        "selector,bound",
        [
            ("#filter", "filterChange"),
            ("#scroll-to-top", "scrollToTop"),
            ("#id-cons", "onConsolidatedClick"),
        ],
    )
    def test_singleton_hooks_are_present(self, page, selector, bound):
        """Each is addressed by id and has no fallback.

        The scripts guard for absence rather than throwing, so losing one
        removes a feature without producing an error anywhere.
        """
        assert page.select_one(selector) is not None, f"{bound} has nothing to bind to"

    def test_nft_preview_is_not_a_template_element(self, page):
        """`nftShowTooltip` builds `#id-nft-preview` and appends it to `<body>`.

        It is script-owned, so the template must not ship one: a pre-rendered
        copy would be found by `nftHideTooltip` and removed on the first hover,
        after which nothing on the page would explain where it went. The
        contract here is the class it is given, asserted in the stylesheet
        tests rather than this one.
        """
        assert page.select_one("#id-nft-preview") is None


class TestCheckboxWrappers:
    """Four toggles, each found through its wrapper rather than directly."""

    @pytest.mark.parametrize(
        "wrapper,does",
        [
            (".switch", "ALGO/USD"),
            (".refresh", "auto-refresh"),
            (".totalnonft", "total without NFTs"),
            (".floor", "NFT floor chart"),
        ],
    )
    def test_wrapper_contains_its_checkbox(self, page, wrapper, does):
        """`$(w).find("input[type=checkbox]")` -- the wrapper is the hook.

        Moving the input out of the wrapper, or the wrapper off the input's
        ancestors, leaves a control that renders and does nothing.
        """
        box = page.select_one(f'{wrapper} input[type="checkbox"]')

        assert box is not None, f"the {does} toggle is unreachable"


class TestValueSpans:
    """Everything `setCurrency` rewrites when the reader switches currency."""

    @pytest.mark.parametrize("cls", ["val", "val6"])
    def test_value_spans_are_spans(self, page, cls):
        """The element name is part of the selector: `span.val`, not `.val`.

        A `<div class="val">` is invisible to the currency switch, so it keeps
        showing ALGO on a page that has switched to USD.
        """
        divs = [el for el in page.select(f".{cls}") if el.tag != "span"]

        assert not divs, f"{len(divs)} .{cls} elements are not <span>"

    @pytest.mark.parametrize("cls", ["val", "val6"])
    def test_value_spans_carry_the_source_number(self, page, cls):
        """`data-val` is the only surviving copy.

        The text is replaced on every switch, so a span without it converts to
        `NaN` the first time and can never recover.
        """
        missing = [el for el in page.select(f"span.{cls}") if not el.has_attr("data-val")]

        assert not missing, f"{len(missing)} span.{cls} without data-val"

    def test_value_spans_hold_no_markup(self, page):
        """`innerHTML` again: a child element survives until the first switch.

        This is the failure that put the total's `sr-only` label outside
        `.pricetip`; the same rule applies to every span the switch rewrites.
        """
        with_children = [
            str(el)[:80] for el in page.select("span.val, span.val6") if el.has_element_children()
        ]

        assert not with_children, f"markup inside rewritten spans: {with_children[:3]}"

    @pytest.mark.parametrize("cls", ["price", "unitprice"])
    def test_in_place_price_controls_carry_both_attributes(self, page, cls):
        """`togglePrice` needs the value and the unit to build either reading.

        Without `data-unit` the flipped label reads "undefined", which looks
        like a data problem rather than a markup one.
        """
        bad = [
            str(el)[:80]
            for el in page.select(f".{cls}")
            if not (el.has_attr("data-val") and el.has_attr("data-unit"))
        ]

        assert not bad, f".{cls} missing data-val/data-unit: {bad[:3]}"


class TestDistributionToggle:
    """`.tdist` opens a panel by id and shades the panel it sits in."""

    def test_every_tdist_names_a_panel(self, page):
        """`$("#" + this.dataset.distid)` -- an empty value selects the page.

        `$("#")` is not an error in jQuery, it is an empty set, so a missing
        distid produces a control that silently does nothing.
        """
        bad = [
            str(el)[:80]
            for el in page.select(".tdist")
            if not (el.get("data-distid") or "").strip()
        ]

        assert not bad, f".tdist without a usable data-distid: {bad[:3]}"

    def test_each_distid_resolves_to_exactly_one_panel(self, page):
        """One control, one panel, both directions.

        A duplicate id makes jQuery toggle only the first, so the second
        control opens someone else's breakdown.
        """
        for control in page.select(".tdist"):
            distid = control["data-distid"]
            panels = page.by_id(distid)

            assert len(panels) == 1, f"{len(panels)} panels for distid {distid}"

    def test_tdist_sits_inside_a_program_panel(self, page):
        """`closest("[data-program-panel]")` is the shading target.

        Found by attribute rather than by `.parent()` on purpose -- which
        element the value span sits directly inside is a layout decision, and
        `.closest(".asar")` breaks on the second click because `asar` is half
        of what the handler toggles.
        """
        orphans = [
            str(el)[:80]
            for el in page.select(".tdist")
            if el.find_parent(attr="data-program-panel") is None
        ]

        assert not orphans, f".tdist outside any program panel: {orphans[:3]}"


class TestAddressableEntries:
    """`.fitem` is how the filter, the reopen memory and the charts find rows."""

    def test_every_entry_has_an_id(self, page):
        """The filter collects ids; `checkOpened` reopens by id after a refresh.

        An entry without one cannot be matched, cannot be reopened, and drops
        out of the filter results without appearing to fail.
        """
        missing = [str(el)[:60] for el in page.select(".fitem") if not el.get("id")]

        assert not missing, f"{len(missing)} .fitem without an id"

    def test_entry_ids_are_unique(self, page):
        """`$("#" + id)` takes the first match.

        Duplicates make the filter reveal one row and leave its twin hidden.
        """
        ids = [el["id"] for el in page.select(".fitem") if el.get("id")]
        dupes = {i for i in ids if ids.count(i) > 1}

        assert not dupes, f"duplicate .fitem ids: {sorted(dupes)[:5]}"

    @pytest.mark.parametrize("section", ["asa", "nft"])
    def test_entries_are_reachable_from_their_section(self, page, section):
        """`$('.' + section + 'sec').find('.fitem')` -- a descendant walk.

        Deliberately not `.children()`: the rows sit inside a wrapper below the
        section heading. Any depth is fine, but leaving the section container
        breaks the reopen-after-refresh memory.
        """
        entries = page.select(f".{section}sec .fitem")

        assert entries, f".{section}sec contains no .fitem entries"

    def test_outermost_entries_carry_the_open_attribute(self, page):
        """`reloadPage` reads `.fitem[open]`, and only `<details>` has it.

        The rule applies to the outermost `.fitem` in each section, not to
        every one: `.fitem` is deliberately nestable -- an asset's body and an
        NFT item are `.fitem` divs inside their entry -- and those inner ones
        are never what the reopen memory stores. An outer entry rebuilt as a
        div would forget its state on every auto-refresh.
        """
        outermost = [
            el
            for el in page.select(".asasec .fitem, .nftsec .fitem")
            if el.find_parent(class_="fitem") is None
        ]
        assert outermost, "no top-level entries found"
        not_details = [(el.get("id"), el.tag) for el in outermost if el.tag != "details"]

        assert not not_details, f"top-level entries that are not <details>: {not_details[:5]}"

    def test_entries_sit_inside_a_section_list(self, page):
        """The filter shows an entry's `.section-list` ancestors along with it.

        Without the ancestor the row is un-hidden inside a container that stays
        hidden, so a search matches and shows nothing.
        """
        orphans = [
            el.get("id")
            for el in page.select(".asasec .fitem, .nftsec .fitem")
            if el.find_parent(class_="section-list") is None
        ]

        assert not orphans, f"entries outside any .section-list: {orphans[:5]}"


class TestPositionIdentity:
    """`data-pid` is how a position is named across a refresh.

    Pinning, deep links and the saved layout all key on it. Everything else the
    markup could offer as a handle -- the value, the amount, the row's place in
    the list -- changes between two loads of the same page, which is the whole
    reason `api.position_id` exists.
    """

    def test_every_position_carries_its_identity(self, page):
        """A position without one drops out of a reader's saved layout.

        Silently: nothing throws, the row renders, and only the pin is gone.
        """
        positions = page.select(".position")
        assert positions, "no .position components rendered"
        missing = [
            str(el)[:80] for el in positions if not (el.get("data-pid") or "").strip()
        ]

        assert not missing, f"{len(missing)} positions without a data-pid"

    def test_identities_are_versioned(self, page):
        """The prefix is what makes a stale stored pin recognisable.

        Change the recipe without bumping it and old pins match nothing, with
        no way to tell that from a position that simply closed.
        """
        from api.position_id import PID_VERSION

        pids = [el["data-pid"] for el in page.select(".position")]

        assert all(pid.startswith(f"{PID_VERSION}-") for pid in pids)

    def test_ambiguity_is_declared_where_it_exists(self, page):
        """Six rows in this bundle share an identity with another row.

        Two Lofty AMM entries, two Cometa stakes, two Gora.fi delegations. The
        attribute is what lets the page say "cannot promise" instead of pinning
        one and hoping.
        """
        by_pid = {}
        for el in page.select(".position"):
            by_pid.setdefault(el["data-pid"], []).append(el)

        for pid, shared in by_pid.items():
            if len(shared) > 1:
                assert all(el.has_attr("data-pid-ambiguous") for el in shared), (
                    f"{pid} names {len(shared)} positions without saying so"
                )

    def test_unambiguous_positions_are_not_flagged(self, page):
        """Otherwise the flag means nothing and the page cannot act on it."""
        by_pid = {}
        for el in page.select(".position"):
            by_pid.setdefault(el["data-pid"], []).append(el)
        wrong = [
            pid
            for pid, shared in by_pid.items()
            if len(shared) == 1 and shared[0].has_attr("data-pid-ambiguous")
        ]

        assert not wrong, f"flagged but unique: {wrong[:5]}"

    def test_the_breakdown_panel_is_addressable_within_one_render(self, page):
        """`data-distid` keeps the loop counter rather than using the pid.

        The panel id only has to be unique on the page, and two ambiguous
        positions share a pid -- keying the DOM id on it would give them the
        same element and the toggle would open the wrong breakdown.
        """
        panels = page.select(".position-breakdown")
        ids = [el.get("id") for el in panels]

        assert all(ids), "a breakdown panel has no id for its control to open"
        assert len(set(ids)) == len(ids), "two breakdown panels share an id"


class TestPositionPresentation:
    """Rows and cards are the same markup with a different area map."""

    def test_the_component_declares_no_presentation(self, page):
        """The inverse of what this once asserted, and the reason matters.

        Placement now comes from `data-layout-position` on the root element,
        because the reader's layout cannot be rendered into this page -- the
        cache entry is shared between signed-in readers, so a modifier written
        here would hand the first reader's choice to everyone after them. See
        `core/tests/test_address_layout.py`.

        Rows is the CSS default, so a `.position` carrying no modifier is fully
        laid out; the hazard the old assertion guarded against is gone rather
        than merely unasserted.
        """
        declared = [
            str(el)[:70]
            for el in page.select(".position")
            if {"position--rows", "position--cards"} & el.classes
        ]

        assert not declared, (
            f"{len(declared)} positions carry a presentation class; the layout "
            "belongs on the root element, not in this cached markup"
        )

    def test_the_summary_comes_before_the_breakdown_in_the_source(self, page):
        """So a screen reader and a keyboard meet the whole before the parts.

        The old row put the breakdown first and pulled it back with `order-1`,
        which reversed the reading order to buy a visual arrangement that named
        grid areas give for nothing.
        """
        for position in page.select(".position"):
            children = [c for c in position.children if c.classes]
            names = [
                "summary" if "position-summary" in c.classes else
                "breakdown" if "position-breakdown" in c.classes else None
                for c in children
            ]
            named = [n for n in names if n]
            if "breakdown" in named:
                assert named.index("summary") < named.index("breakdown")


class TestNftPairing:
    """The thumbnail-to-entry link the filter depends on."""

    def test_thumbnails_use_the_t_prefixed_id_of_their_entry(self, page):
        """`showMatchedNodes` shows an icon only when its id is `"t" + entry id`.

        Break the pairing and filtering an NFT collection shows the row with a
        blank space where the image was -- the one failure mode here that a
        reader would notice but never be able to explain.
        """
        icons = [el for el in page.select(".nfticon") if el.get("id")]
        assert icons, "no .nfticon carries an id"

        entry_ids = {el["id"] for el in page.select(".fitem") if el.get("id")}
        unpaired = [
            el["id"] for el in icons if el["id"][1:] not in entry_ids or el["id"][0] != "t"
        ]

        assert not unpaired, f"thumbnails with no matching entry: {unpaired[:5]}"

    def test_thumbnails_carry_the_full_image_path(self, page):
        """`nftShowTooltip` reads `data-path` to build the hover preview."""
        missing = [
            el.get("id") for el in page.select(".nfticon") if not el.get("data-path")
        ]

        assert not missing, f"{len(missing)} .nfticon without data-path"

    def test_deferred_images_keep_the_bare_class_name(self, page):
        """`deferImages` uses `getElementsByClassName('nft')`, not a selector.

        The bare token has to be present: renaming to `nft-thumb` leaves every
        full-size NFT image on its placeholder for good.
        """
        deferred = page.select("img.nft[data-src]")

        assert deferred, "no img.nft[data-src] for deferImages to load"


class TestItemHeaders:
    """Two click bindings distinguished only by a modifier class."""

    @pytest.mark.parametrize(
        "selector,fills",
        [(".token.item-header", "showExpiry"), (".nft.item-header", "showTimes")],
    )
    def test_modifier_and_base_class_share_an_element(self, page, selector, fills):
        """`$(".token.item-header")` needs both tokens on the same element.

        Splitting them across a wrapper and its child matches nothing, and the
        elapsed-time and expiry spans stay empty.
        """
        assert page.select(selector), f"{fills} has no header to bind to"

    def test_epoch_spans_carry_their_timestamp(self, page):
        """Both handlers read `data-epoch` and write the rendered text in.

        A span without it renders as a permanent blank, because the server
        deliberately sends no fallback text.
        """
        spans = page.select(".epoch")
        if not spans:
            pytest.skip("payload has no timestamped entries")
        missing = [str(el)[:60] for el in spans if not el.get("data-epoch")]

        assert not missing, f"{len(missing)} .epoch without data-epoch"


class TestCharts:
    """Payload blocks, canvases and the wrappers the floor switch moves."""

    @pytest.mark.parametrize(
        "name",
        ["asachart", "nftchart", "ratiochart", "nftfloorchart", "distchart", "consolidated"],
    )
    def test_json_payload_block_is_present_and_parses(self, page, name):
        """`parseJsonScript` calls `JSON.parse` on the block's text.

        A renamed id yields `null` and the chart draws nothing; malformed JSON
        throws inside `mainAddress` and takes the filter, the currency switch
        and every later binding down with it.
        """
        import json

        block = page.select_one(f"script#{name}")
        assert block is not None, f"no JSON payload block #{name}"
        json.loads(block.text(strip=False))

    @pytest.mark.parametrize(
        "name",
        ["distchart", "ratiochart", "ratiochartfloor", "asachart", "nftchart", "nftfloorchart"],
    )
    def test_canvas_and_legend_container_pair_up(self, page, name):
        """Each chart is `#id-<name>` with its legend at `#id-legend-<name>`.

        The legend id is passed through the chart's plugin options, so a
        mismatch produces a chart with no legend and no error.
        """
        assert page.select_one(f"#id-{name}") is not None
        assert page.select_one(f"#id-legend-{name}") is not None

    @pytest.mark.parametrize(
        "wrapper", ["id-chart-ratio", "id-chart-ratiofloor", "id-chart-nft", "id-chart-nftfloor"]
    )
    def test_floor_switch_has_all_four_wrappers(self, page, wrapper):
        """`setNftFloor` returns early unless all four are present.

        Losing one disables the whole estimate/floor swap rather than half of
        it -- the guard is deliberately all-or-nothing so a partial layout
        cannot leave two charts stacked on each other.
        """
        assert page.select_one(f"#{wrapper}") is not None


class TestConsolidated:
    """The summary header the charts and the open/closed memory read."""

    @pytest.mark.parametrize(
        "attribute", ["data-balance", "data-staked", "data-liquidity", "data-defi"]
    )
    def test_header_carries_each_category_total(self, page, attribute):
        """`updateDistChart` reads these to rebuild the stacked bar.

        They are the only machine-readable copy; the rendered figures beside
        them are formatted for people and get rewritten by the currency switch.
        """
        assert page.select_one("#id-cons-header").has_attr(attribute)

    def test_body_is_addressable_for_the_open_memory(self, page):
        """`onConsolidatedClick` stores whether the section was left open."""
        assert page.select_one("#id-cons-body") is not None


class TestChartClickTargets:
    """What `chartClick` matches a slice label against.

    This one is on notice rather than protected: the handler reaches its
    header with `unit.parent().parent()` and then tests `.hasClass("active")`,
    a Materialize class no template on this page emits. The depth assumption
    breaks on any re-nesting and the class test is already dead, which is why
    SELECTOR_CONTRACT.md lists it under known-fragile. The test below pins only
    the part worth keeping -- that a slice label has something to match.
    """

    def test_unit_labels_exist_for_slice_matching(self, page):
        """`$(".unit").filter(text === label)` is the only link chart -> row.

        Without it a chart click silently does nothing: the handler returns
        early when nothing matches, which is there for the "others" slice but
        swallows every other miss just as quietly.
        """
        units = [el.text() for el in page.select(".unit")]

        assert units, "no .unit labels for chartClick to match against"

    def test_unit_label_text_matches_the_chart_labels(self, page, sample_payload):  # noqa: F811
        """The match is on exact text, so formatting the label breaks it.

        A slice is labelled with the asset's unit name; wrapping the rendered
        unit in extra text -- a prefix, a separator, a nested badge -- makes
        `text === label` false for every asset at once.
        """
        units = {el.text() for el in page.select(".unit")}
        expected = {item["asset"]["unit"] for item in sample_payload["asaitems"]}
        missing = expected - units

        assert not missing, f"chart labels with no matching .unit: {sorted(missing)[:5]}"


class TestSiteWideControls:
    """Bound in site.js, so they outlive any address-page redesign."""

    def test_copy_controls_are_present(self, page):
        """`$(".copy").on("click", copyToClipboard)` lives in site.js.

        Renaming it here breaks a binding that is not in address.js at all,
        which is exactly the kind of cross-file coupling worth writing down.
        """
        assert page.select(".copy"), "no .copy controls on the page"
