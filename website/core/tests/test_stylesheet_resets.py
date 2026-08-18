"""Declarations the framework's reset removes, and we have to put back.

Tailwind's preflight zeroes `margin` and `padding` on `*`, `::before`,
`::after` and `::backdrop`. That is deliberate and mostly welcome, but it is
indiscriminate: it also takes out declarations the UA stylesheet uses to
position browser-owned UI, and losing one of those does not look like a broken
stylesheet -- it looks like a bug in the feature.

`margin: auto` on a modal `<dialog>` is the case that bit us. It is the single
declaration that centres a dialog in the viewport, so with it gone the login
modal opened pinned to the top-left corner, on every page, in every theme.
Nothing failed; it just looked wrong, and the cause was three layers away from
anything anyone would think to read.

These assert against the built stylesheet rather than `input.css`, because the
build is what ships: a rule that Lightning CSS drops, or that a future
`source()` change stops emitting, is exactly the regression worth catching.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

#: The build output every page loads.
STYLESHEET = Path(settings.STATICFILES_DIRS[0]) / "css" / "style.tw.css"


@pytest.fixture(scope="module")
def stylesheet():
    if not STYLESHEET.is_file():
        pytest.skip(f"{STYLESHEET} has not been built")
    return STYLESHEET.read_text()


class TestCoreStylesheetResets:
    """Testing class for reset damage the stylesheet has to undo."""

    def test_core_stylesheet_preflight_still_zeroes_every_margin(self, stylesheet):
        """The premise. If this stops being true the rules below are dead weight.

        Asserted rather than assumed, so that a Tailwind upgrade which narrows
        the reset shows up here as a failing premise instead of leaving a
        compensating rule in place with nothing left to compensate for.
        """
        assert re.search(r"\*,[^{}]*\{[^{}]*margin:\s*0", stylesheet), (
            "preflight no longer zeroes margin on `*` -- re-check whether the "
            "dialog rule below is still needed"
        )

    def test_core_stylesheet_centres_a_modal_dialog(self, stylesheet):
        """Without this the login and confirm modals open in the top-left."""
        assert re.search(r"dialog:modal\s*\{[^{}]*margin:\s*auto", stylesheet)

    def test_core_stylesheet_leaves_non_modal_dialogs_alone(self, stylesheet):
        """A `show()` dialog is positioned by its author, not centred by us.

        The rule is scoped to `:modal` for that reason; a bare `dialog`
        selector would move any inline dialog added later.
        """
        assert not re.search(r"(?<![-\w:])dialog\s*\{[^{}]*margin:\s*auto", stylesheet)

    @pytest.mark.parametrize("level", ["h1", "h2", "h3", "h4", "h5", "h6"])
    def test_core_stylesheet_gives_every_heading_a_size(self, stylesheet, level):
        """Without this an h1 is a paragraph in bold-ish clothing.

        Preflight sets `font-size: inherit; font-weight: inherit` on h1..h6 --
        a deliberate choice, on the reasoning that a design system supplies its
        own scale. We supplied only the family for a while, so every page that
        did not add utilities of its own rendered its headings at body size:
        features, tokenomics, faq, about and the error pages all did.

        Parametrised, so a partial scale fails with the level named.
        """
        assert re.search(
            rf"(?:^|[,}}]){level}\{{[^}}]*font-size:", stylesheet
        ), f"{level} has no size in the built stylesheet"

    def test_core_stylesheet_heading_scale_descends(self, stylesheet):
        """h1 must not be smaller than h3, whatever the numbers are.

        The sizes themselves are a design decision and may change; that they
        get smaller as the level grows is what makes them a hierarchy.
        """
        sizes = []
        for level in ("h1", "h2", "h3", "h4", "h5", "h6"):
            match = re.search(
                rf"(?:^|[,}}]){level}\{{[^}}]*font-size:([0-9.]+)rem", stylesheet
            )
            assert match, f"{level} has no rem size to compare"
            sizes.append(float(match.group(1)))

        assert sizes == sorted(sizes, reverse=True), (
            f"the scale is not descending: {sizes}"
        )

    def test_core_stylesheet_headings_can_still_be_overridden(self, stylesheet):
        """A card header at `text-base` has to beat the base scale.

        Base is the lowest layer, so utilities win -- but only while the scale
        stays in `@layer base`. Written outside it, these rules would out-rank
        every `text-*` utility in the project and there would be no way to opt
        out of them, which is what the profile card headers rely on.
        """
        heading = re.search(r"(?:^|[,}])h1\{[^}]*font-size:", stylesheet)
        assert heading, "no h1 size to place"

        assert heading.start() < stylesheet.index(".text-base{"), (
            "the heading scale is emitted after the utilities, so `text-base` "
            "can no longer override it"
        )

    def test_core_stylesheet_asset_rows_have_a_stripe_to_colour(self, stylesheet):
        """The colour rules are useless without a border to put them on.

        Each row carries a 4px left stripe whose colour matches that asset's
        slice in the pie chart above -- the only thing tying a row to its share
        of the portfolio. The width was declared on `.collapsible-header`, a
        Materialize class the markup stopped emitting when the address page was
        converted, so seventeen colour rules were setting `border-left-color`
        on a border with no width and every stripe was invisible.

        Nothing failed: the rows rendered, the colours were in the stylesheet,
        and the only symptom was a missing 4px line nobody could test for.
        """
        assert re.search(
            r"\.token\.item-header[^{]*\{[^}]*border-left:\s*4px", stylesheet
        ), "asset rows have no left stripe"
        assert re.search(
            r"\.nft\.item-header[^{]*\{[^}]*border-left:\s*4px", stylesheet
        ), "collection rows have no left stripe"

    @pytest.mark.parametrize("slot", ["calgo", "c0", "c7", "c15"])
    def test_core_stylesheet_stripe_slots_feed_the_border(self, stylesheet, slot):
        """A slot must set the property the border actually reads.

        Setting `border-left-color` worked only while the width lived in the
        same rule; routed through `--stripe`, the two cannot drift apart again.
        """
        match = re.search(rf"\.token\.{slot}\{{([^}}]*)\}}", stylesheet)

        assert match, f"no rule for slot {slot}"
        assert "--stripe:" in match.group(1), (
            f"slot {slot} sets something other than the stripe colour"
        )

    def test_core_stylesheet_keeps_no_collapsible_rules(self, stylesheet):
        """`collapsible` is Materialize's; the address page stopped emitting it.

        Rules left behind for a class nothing renders are how the stripe came
        to be dead -- they look like working styling in the source.
        """
        assert "collapsible" not in stylesheet

    def test_core_stylesheet_positions_the_nft_preview(self, stylesheet):
        """The hover preview is a popup only if something positions it.

        In production this was a Materialize tooltip, so its whole appearance
        came from `.material-tooltip`. address.js builds the element itself
        now and writes `top`/`left` on it -- which do nothing at all while the
        element is `position: static`, so the full-size image landed at the
        end of the document instead of beside the thumbnail. The markup was
        right, the handler ran, and the feature was simply gone.
        """
        match = re.search(r"\.nftpreview\{([^}]*)\}", stylesheet)

        assert match, "the preview has no styling, so it cannot appear as a popup"
        assert "position:absolute" in match.group(1).replace(" ", ""), (
            "the preview is not positioned, so its coordinates do nothing"
        )

    def test_core_stylesheet_preview_does_not_eat_its_own_events(self, stylesheet):
        """It opens under the cursor, so it must not receive the pointer.

        Otherwise it swallows the mouseover and the click that dismisses it,
        and flickers as the pointer crosses the popup it just opened.
        """
        match = re.search(r"\.nftpreview\{([^}]*)\}", stylesheet)

        assert "pointer-events:none" in match.group(1).replace(" ", "")

    def test_core_stylesheet_preview_follows_the_theme(self, stylesheet):
        """It is chrome, not chart data, so it takes the reader's theme."""
        body = re.search(r"\.nftpreview\{([^}]*)\}", stylesheet).group(1)

        assert "var(--color-base-100)" in body
        assert "var(--color-base-300)" in body

    def test_core_stylesheet_reset_strips_bare_form_controls(self, stylesheet):
        """The premise for the rule the widget needs.

        Preflight clears `background-color` and `border` from every `input`,
        on the reasoning that a design system draws its own fields. Asserted so
        that a Tailwind upgrade which stops doing it shows up here rather than
        leaving a compensating rule in place with nothing to compensate for.
        """
        match = re.search(
            r"button,input,select,optgroup,textarea\{([^}]*)\}", stylesheet
        )

        assert match, "preflight no longer resets form controls as a group"
        assert "background-color:#0000" in match.group(1).replace(" ", "")
