"""Naming a position's breakdown panel, when its `pid` cannot name it.

Recorded as a known bug when `pq-`/`pv-` ids were added and not fixed then:
the markup declined to give an ambiguous position an id, then used its shared
`pid` for the breakdown panel two lines later, so expanding one position opened
the other one's breakdown.
"""

import re

import pytest
from django.template.loader import render_to_string

from core.templatetags.core_extras import breakdown_key


class TestBreakdownKeyFilter:
    """Testing class for :py:func:`core.templatetags.core_extras.breakdown_key`."""

    def test_core_extras_breakdown_key_uses_the_pid_when_it_is_unique(self):
        """185 of 190 positions on the reference bundle land here, and keeping
        their stable identity is why the fallback is not used for everyone."""
        assert breakdown_key({"pid": "p1-31566704-abc"}, "1-1") == "p1-31566704-abc"

    def test_core_extras_breakdown_key_declines_an_ambiguous_pid(self):
        """**The bug.** Two indistinguishable positions share one `pid`, so it
        cannot name either of their panels."""
        program = {"pid": "p1-31566704-abc", "pid_ambiguous": True}

        assert breakdown_key(program, "1-1") != "p1-31566704-abc"

    def test_core_extras_breakdown_key_separates_an_ambiguous_pair(self):
        """The two positions must end up with different keys, which is the
        whole point - same pid, different place in the render."""
        program = {"pid": "p1-31566704-abc", "pid_ambiguous": True}

        assert breakdown_key(program, "1-1") != breakdown_key(program, "2-1")

    def test_core_extras_breakdown_key_falls_back_without_a_pid(self):
        assert breakdown_key({}, "1-2") == "n1-2"

    def test_core_extras_breakdown_key_survives_a_missing_program(self):
        """**A filter argument that is None must not 500 the page.**

        `|filter:a.b` on a null `a` takes the whole address page down while
        `{{ a.b }}` renders empty, which this project has already been bitten
        by once.
        """
        assert breakdown_key(None, "1-1") == "n1-1"


@pytest.mark.django_db
class TestPositionBreakdownMarkup:
    """The rendered markup, which is where the collision actually showed."""

    def _render(self, pid, ambiguous, counter):
        return render_to_string(
            "snippets/dynamic/position.html",
            {
                "prog": {
                    "pid": pid,
                    "pid_ambiguous": ambiguous,
                    "value": 1.5,
                    "amount": 2,
                    "program": {"type": "Staked", "name": "A farm", "code": "x"},
                    "distribution": [{"name": "part", "value": 1.5}],
                },
                "asset": {"id": 31566704, "decimals": 6, "unit": "USDC"},
                "counter": counter,
            },
        )

    def _ids(self, html):
        """Return the panel id and the button's pointer at it."""
        panel = re.search(r'<div id="(dist-[^"]+)"', html)
        button = re.search(r'data-distid="(dist-[^"]+)"', html)
        return panel.group(1), button.group(1)

    def test_core_position_button_and_panel_agree(self):
        """They are rendered 40 lines apart from what used to be two separate
        expressions; a fragment of a mismatch is a control that opens nothing."""
        panel, button = self._ids(self._render("p1-31566704-abc", False, "1-1"))

        assert panel == button

    def test_core_position_ambiguous_pair_do_not_collide(self):
        """**The reported behaviour: expanding one opened the other.**

        Same `pid`, because they are indistinguishable. Different panels,
        because they are different positions.
        """
        first, _ = self._ids(self._render("p1-31566704-abc", True, "1-1"))
        second, _ = self._ids(self._render("p1-31566704-abc", True, "2-1"))

        assert first != second

    def test_core_position_ambiguous_still_gets_no_swap_id(self):
        """The fix must not undo what `a1bdf9a` was careful about: an ambiguous
        position gets no `pq-`/`pv-` id, because two elements under one id means
        a swap corrects the wrong money."""
        html = self._render("p1-31566704-abc", True, "1-1")

        assert 'id="pv-' not in html
        assert 'id="pq-' not in html

    def test_core_position_unambiguous_keeps_its_swap_ids(self):
        html = self._render("p1-31566704-abc", False, "1-1")

        assert 'id="pv-p1-31566704-abc"' in html
        assert 'id="pq-p1-31566704-abc"' in html
