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
