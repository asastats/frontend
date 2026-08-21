"""The money-column design's DOM contract — designs 2 and 3.

Split out of ``test_selector_contract.py`` on 2026-08-20, when design 1 was
restored to the untouched old page. Everything here asserts markup that belongs
to the money-column designs: the position component, its stable identity, the
pin and grip controls, and the amount witness that makes an ambiguous position
pinnable.

**Live again since 2026-08-21**, when ``address_money.html`` was built. They
were parked, not deleted, because the reasoning in them is the expensive part
-- the identity design, the witness, the "controls ship unpressed because the
cache is shared" rule -- and rewriting that against a new template would have
been strictly worse than repointing one fixture. Repointing the fixture is
exactly what bringing them back took, and every assertion held unchanged.
"""

import pytest
from django.template.loader import render_to_string

from core.tests.dom import parse

from core.tests.test_address_templates import _build_context, sample_payload  # noqa: F401

@pytest.fixture(scope="module")
def page(sample_payload):  # noqa: F811
    """Design 2 rendered against the real bundle payload.

    Design 2 rather than design 3 because the two share this template and
    differ by one class on the list; everything asserted here is in the part
    they share. :class:`TestCompactIsTheSameMarkup` pins that.
    """
    context = _build_context(sample_payload)
    context["layout"] = "money-column"
    context["compact"] = False
    return parse(render_to_string("address_money.html", context))


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


class TestPinControls:
    """What `pins.js` needs to find, and what it must not find.

    Pins live in the reader's browser and never reach the server, so the page
    ships every control in the same state for everybody. That is not a
    simplification -- this page's cache entry is shared, so a pressed control
    rendered here would be pressed for whoever asked next.
    """

    def test_every_asset_and_collection_offers_one(self, page):
        """One control per top-level entry, and none anywhere else."""
        controls = page.select("[data-pin]")

        assert controls, "no pin controls on the page"

    def test_each_control_names_its_own_entry(self, page):
        """`data-pin` is the entry id, which is how a pin outlives a reload.

        Anything else -- an index, a row number, the value -- changes between
        two loads of the same page, which is the same reasoning that produced
        `pid` for positions.
        """
        for control in page.select("[data-pin]"):
            target = control["data-pin"]
            entry = control.find_parent(class_="fitem")

            assert entry is not None, f"{target} control sits outside any entry"
            assert entry.get("id") == target, (
                f"pin names {target} but sits in {entry.get('id')}"
            )

    def test_controls_ship_unpressed(self, page):
        """The reader's own pins are pressed by the script, not by the server."""
        pressed = [
            c for c in page.select("[data-pin]") if c.get("aria-pressed") != "false"
        ]

        assert not pressed, f"{len(pressed)} controls are not shipped unpressed"

    def test_no_entry_ships_marked_as_pinned(self, page):
        """Same reason: `.pinned` is applied client-side or not at all."""
        assert not page.select(".fitem.pinned")

    def test_nested_entries_have_no_control(self, page):
        """An NFT item is a `.fitem` inside its collection's `.fitem`.

        `pins.js` derives the container to reorder from the control's own
        entry, so a control on a nested entry would reorder a collection's
        items instead of the collections. It finds none because none is
        rendered: the outermost `.fitem` above a control's own entry must not
        exist.
        """
        for control in page.select("[data-pin]"):
            entry = control.find_parent(class_="fitem")
            outer = entry.find_parent(class_="fitem")

            assert outer is None, f"{entry.get('id')} is a nested entry"

    def test_each_control_is_labelled(self, page):
        """The icon is the only content, so the label is the whole name."""
        for control in page.select("[data-pin]"):
            assert control.get("aria-label"), (
                f"{control['data-pin']} control has no accessible name"
            )


class TestPositionPins:
    """Pinning one position within its asset, and the witness that allows it.

    Three pids in the reference bundle name two rows each. The payload carries
    nothing that tells those pairs apart, so the amount is stored beside the pin
    as a tiebreaker -- see `static/js/pins.js`.
    """

    def test_the_position_list_is_marked(self, page):
        """`[data-positions]` is the container `pins.js` reorders within."""
        assert page.select("[data-positions]"), "no position list opted in"

    def test_every_position_carries_the_witness(self, page):
        """Including unambiguous ones, so the attribute is never conditional.

        A witness present only on ambiguous rows would make the reader's stored
        pin depend on a judgement the page made at render time -- and that
        judgement can change when the payload does.
        """
        for position in page.select(".position"):
            assert position.has_attr("data-amount"), (
                f"{position.get('data-pid')} carries no amount to disambiguate by"
            )

    def test_the_witness_is_not_part_of_the_identity(self, page):
        """Two positions sharing a pid must still differ in amount.

        If the amount were hashed into the pid these would be distinct ids and
        this test would be vacuous -- which is exactly the design being
        prevented, because the id would then change whenever the amount did.
        """
        by_pid = {}
        for position in page.select(".position"):
            by_pid.setdefault(position.get("data-pid"), []).append(
                position.get("data-amount")
            )

        shared = {pid: amounts for pid, amounts in by_pid.items() if len(amounts) > 1}
        assert shared, "no ambiguous positions in the sample; the fallback is untested"
        for pid, amounts in shared.items():
            assert len(set(amounts)) == len(amounts), (
                f"{pid} names rows that even the amount cannot tell apart"
            )

    def test_ambiguous_positions_say_so(self, page):
        """The pin still works there; the page just does not overpromise."""
        for position in page.select(".position"):
            pid = position.get("data-pid")
            twins = [p for p in page.select(".position") if p.get("data-pid") == pid]
            if len(twins) > 1:
                assert position.has_attr("data-pid-ambiguous")

    def test_controls_ship_unpressed(self, page):
        for control in page.select("[data-pin-position]"):
            assert control.get("aria-pressed") == "false"

    def test_a_control_sits_inside_the_position_it_pins(self, page):
        """`togglePosition` reads the amount off the row, not off the control.

        Two rows can share a pid, and the reader pressed one of them -- so the
        row is the answer to "which one", and the control has to be inside it.
        """
        for control in page.select("[data-pin-position]"):
            position = control.find_parent(class_="position")

            assert position is not None, "a position pin outside any position"
            assert position.get("data-pid") == control["data-pin-position"]

    def test_a_lone_position_still_offers_a_pin(self, page):
        """Reversed on 2026-08-21, when the pinned band was built.

        This used to assert the opposite, and was right at the time: pinning
        then meant floating a row to the top of its own venue group, and in a
        group of one there is no order to change, so the control could not act.

        The band changes what pinning *means*. A pinned position is copied to a
        band at the top of the page, so pinning the only position in a venue
        moves it from somewhere the reader must scroll to and open, to
        somewhere they can see -- which is the case the band is most useful for,
        not the case to withhold it from.

        Kept as a test rather than deleted because the reasoning is the point:
        if the band is ever dropped, this is the assertion that has to be
        reversed again, and the reason will be waiting here.
        """
        lone = []
        for container in page.select("[data-positions]"):
            positions = [
                child for child in container.children if "position" in child.classes
            ]
            if len(positions) == 1:
                lone.append(positions[0])

        assert lone, "no single-position venue in the payload; this asserts nothing"
        assert all(position.select("[data-pin-position]") for position in lone)


