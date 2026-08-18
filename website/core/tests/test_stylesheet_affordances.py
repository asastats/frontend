"""Controls that look like text unless something says otherwise.

Three of the address page's controls are bare `<span>`s with a click handler
bound in address.js: `.tdist` opens a program's distribution panel, `.price`
and `.unitprice` flip a price around. They have no href, no button chrome and
no role -- the only thing separating them from the numbers beside them is
whatever the stylesheet gives them.

Materialize gave them a dotted underline and a hover colour. The DaisyUI
conversion carried over `cursor-pointer` and nothing else, so for the whole of
the redesign they rendered as plain text: invisible to anyone who had not
already put a pointer on them, and completely silent on a touch screen. No
test failed, because every one of them still worked when clicked.

That is the regression these guard. They assert against the built stylesheet
rather than `input.css`, because the build is what ships -- a rule Lightning
CSS drops, or that a future `source()` change stops emitting, is exactly the
loss worth catching.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

#: The build output every page loads.
STYLESHEET = Path(settings.STATICFILES_DIRS[0]) / "css" / "style.tw.css"

#: The three click targets that render as bare text.
IN_PLACE_CONTROLS = ["tdist", "price", "unitprice"]


@pytest.fixture(scope="module")
def stylesheet():
    if not STYLESHEET.is_file():
        pytest.skip(f"{STYLESHEET} has not been built")
    return STYLESHEET.read_text()


def rules_for(stylesheet, selector):
    """Return every declaration block whose selector list contains `selector`.

    The build groups selectors and splits one authored rule across several
    output rules, so a control's declarations are spread over more than one
    block and have to be gathered before they can be asserted on.

    :param stylesheet: the built stylesheet
    :type stylesheet: str
    :param selector: a full selector, e.g. ``.tdist`` or ``.tdist:hover``
    :type selector: str
    :return: str
    """
    # `$` as well as a delimiter: the selector is often last in its list, and
    # the head is everything up to the brace, so there is nothing after it.
    pattern = re.escape(selector) + r"(?=[,{]|$)"
    return " ".join(
        match.group(1)
        for match in re.finditer(r"\{([^{}]*)\}", stylesheet)
        for head in [stylesheet[: match.start()].rsplit("}", 1)[-1]]
        if re.search(pattern, head)
    )


class TestCoreStylesheetAffordances:
    """Testing class for the resting and hover cues on text-shaped controls."""

    @pytest.mark.parametrize("control", IN_PLACE_CONTROLS)
    def test_core_stylesheet_in_place_control_is_marked_at_rest(
        self, stylesheet, control
    ):
        """A cursor is not an affordance: it needs a pointer already on it.

        This is the state the conversion lost, and the one that matters most --
        it is what tells a reader the value does something before they touch it.
        """
        body = rules_for(stylesheet, f".{control}")

        assert "text-decoration" in body, (
            f".{control} has no decoration at rest, so it renders as plain text"
        )

    @pytest.mark.parametrize("control", IN_PLACE_CONTROLS)
    def test_core_stylesheet_in_place_control_is_dotted_at_rest(
        self, stylesheet, control
    ):
        """Dotted, because it acts here rather than navigating away.

        Links get no underline until hover (DaisyUI's `link-hover`), so a solid
        resting underline would read as a link that goes somewhere. The dots
        are what keep the two apart while both are at rest.
        """
        body = rules_for(stylesheet, f".{control}")

        assert "dotted" in body, f".{control} is not distinguishable from a link"

    @pytest.mark.parametrize("control", IN_PLACE_CONTROLS)
    def test_core_stylesheet_in_place_control_resolves_on_hover(
        self, stylesheet, control
    ):
        """And on hover it becomes exactly what a link becomes.

        The two idioms converge under the pointer, which is where "you can
        click this" needs saying, and stay distinct everywhere else.
        """
        body = rules_for(stylesheet, f".{control}:hover")

        assert "solid" in body, f".{control} does not respond to hover"

    @pytest.mark.parametrize("control", IN_PLACE_CONTROLS)
    def test_core_stylesheet_in_place_control_answers_a_tap(
        self, stylesheet, control
    ):
        """`:hover` is the wrong hook on touch -- it sticks after the tap.

        Without an `:active` state a touch reader gets no acknowledgement that
        the tap landed, on a control whose whole job is to reveal something.
        """
        body = rules_for(stylesheet, f".{control}:active")

        assert "solid" in body, f".{control} gives no feedback to a tap"

    def test_core_stylesheet_hover_states_are_gated_on_a_real_pointer(
        self, stylesheet
    ):
        """Otherwise a tapped row stays in its hover state until you tap away.

        The `:active` rules above are what serve touch; these have to be kept
        away from it.
        """
        assert re.search(
            r"@media\s*\(hover:\s*hover\)\s*and\s*\(pointer:\s*fine\)\s*\{"
            r"[^{}]*\.tdist:hover",
            stylesheet,
        ), "hover styling is not gated on a fine pointer"

    def test_core_stylesheet_in_place_controls_set_no_colour(self, stylesheet):
        """Because `text-error` has to keep winning on negative values.

        `.tdist` renders with `text-error` on Borrowed, Loss and Debt programs,
        where the red is the only thing marking the row as a liability. Setting
        a colour here -- the obvious way to make these look like links -- would
        take it away on hover, on exactly the rows least able to spare it.
        Declaring decoration alone lets the red flow through to the underline
        via `currentColor` instead.
        """
        for control in IN_PLACE_CONTROLS:
            for state in ("", ":hover", ":active"):
                body = rules_for(stylesheet, f".{control}{state}")

                assert not re.search(r"(?<![-\w])color:", body), (
                    f".{control}{state} sets a colour, which will override "
                    "`text-error` on negative-value rows"
                )

    def test_core_stylesheet_copy_control_uses_opacity_not_colour(self, stylesheet):
        """`.copy` is a clipboard emoji, and an emoji ignores `color`.

        It carries its own colours, so the hover cue every other control gets
        would do nothing at all here. Opacity is the one channel it answers to.
        """
        body = rules_for(stylesheet, ".copy:hover")

        assert "opacity" in body, ".copy has no hover response"

    def test_core_stylesheet_in_place_controls_can_take_focus_styling(
        self, stylesheet
    ):
        """They are not keyboard-reachable yet; this is so they can be.

        They are spans with a click handler, so no `tabindex` means no focus
        and no keyboard operation. Keeping the ring here means adding the
        attributes to the templates is a one-line change rather than a one-line
        change plus a control that focuses invisibly.
        """
        body = rules_for(stylesheet, ".tdist:focus-visible")

        assert "outline" in body, "focusing a .tdist would show nothing"

    def test_core_stylesheet_links_keep_the_framework_idiom(self, stylesheet):
        """The in-place controls were matched to links, not the other way round.

        `link-hover` is what all 87 of the site's links carry, and colouring
        them was rejected on measurement: `--color-primary` fails WCAG AA
        against `--color-base-100` on 27 of the 57 themes we ship, our own
        brand theme among them at 2.16:1. If this ever stops being DaisyUI's
        plain underline-on-hover, the dotted/solid pairing above no longer
        converges on anything and needs rethinking.
        """
        assert re.search(r"\.link-hover:hover\{[^}]*text-decoration-line:underline", stylesheet)
        assert re.search(r"\.link-hover\{[^}]*text-decoration-line:none", stylesheet)
