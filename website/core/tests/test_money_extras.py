"""The two template filters the money-column designs are built on.

:func:`program_groups` stacks an asset's positions under their program,
and :func:`allocation_bands` computes the five categories that the allocation
bar, the five figures and the ratio donut all draw from.

Both are presentation, which is why they are filters rather than view context:
design 1 renders the same payload ungrouped, and the serialized payload is
shared with the JSON API, which must not grow a website-shaped key.
"""

from collections import namedtuple

import pytest

from core.templatetags.core_extras import allocation_bands, program_groups

#: Stands in for `utils.structs.Consolidated` without importing the real one,
#: so these tests fail on a field rename rather than following it silently.
Totals = namedtuple("Totals", ["balance", "staked", "liquidity", "defi", "nftfloor"])


def _program(name, value, url=None, type_="Balance"):
    """Build one entry of an asaitem's ``programs`` list."""
    return {
        "program": {"name": name, "url": url, "type": type_},
        "value": value,
    }


class TestProgramGroups:
    """Grouping an asset's positions by the program holding them.

    By program, not by venue. `program.name` is a venue for most position types
    but the category "Liquidity" for LP positions, whose venue is inside
    `program.code` -- so the reference address puts 18 LP positions across five
    venues under one heading. Naming it a venue grouping would be a claim the
    payload does not support.
    """

    def test_positions_under_one_program_are_one_group(self):
        groups = program_groups([_program("Tinyman2", 5), _program("Tinyman2", 3)])

        assert len(groups) == 1
        assert len(groups[0]["positions"]) == 2

    def test_the_subtotal_is_the_sum_of_the_group(self):
        """The number a reader would otherwise add up themselves."""
        groups = program_groups([_program("Tinyman2", 5), _program("Tinyman2", 3)])

        assert groups[0]["total"] == 8

    def test_groups_keep_their_first_appearance_order(self):
        """Not value order.

        The payload arrives ordered by the engine, and re-sorting here would put
        the subtotal ordering at odds with the position ordering inside each
        group for no gain. The toolbar sorts, later, and sorts both together.
        """
        groups = program_groups(
            [_program("Pact", 1), _program("Tinyman2", 99), _program("Pact", 1)]
        )

        assert [group["name"] for group in groups] == ["Pact", "Tinyman2"]

    def test_a_nameless_position_is_its_own_group(self):
        """A bare holding names no program, and the template labels it."""
        groups = program_groups([_program("", 4), _program("Pact", 1)])

        assert groups[0]["name"] == ""
        assert groups[0]["total"] == 4

    def test_a_missing_program_block_does_not_lose_the_position(self):
        groups = program_groups([{"value": 2}])

        assert len(groups) == 1
        assert len(groups[0]["positions"]) == 1

    def test_a_missing_value_contributes_nothing(self):
        """`None` coerces cleanly to zero and never reaches the guard below."""
        groups = program_groups([_program("Pact", 5), _program("Pact", None)])

        assert groups[0]["total"] == 5
        assert len(groups[0]["positions"]) == 2

    def test_an_unevaluated_value_costs_only_itself(self):
        """One bad number must not discard the whole group's arithmetic.

        This needs a value `float()` actually rejects. An earlier version of
        this test passed `None`, which becomes `0.0` without raising -- so it
        asserted the right thing while exercising none of the code that makes it
        true, and the `except` arm stayed uncovered.
        """
        groups = program_groups([_program("Pact", 5), _program("Pact", "n/a")])

        assert groups[0]["total"] == 5
        assert len(groups[0]["positions"]) == 2

    def test_an_unevaluated_value_does_not_stop_later_ones_counting(self):
        """The guard skips one addend, not the rest of the loop."""
        groups = program_groups(
            [_program("Pact", 5), _program("Pact", "n/a"), _program("Pact", 3)]
        )

        assert groups[0]["total"] == 8

    def test_the_program_url_is_carried_through(self):
        groups = program_groups([_program("Pact", 1, url="https://pact.fi")])

        assert groups[0]["url"] == "https://pact.fi"

    @pytest.mark.parametrize("programs", [None, [], ()])
    def test_nothing_to_group_yields_nothing(self, programs):
        assert program_groups(programs) == []


class TestAllocationBands:
    """The five categories, computed once for three drawings of them."""

    def test_the_five_categories_are_always_present(self):
        """Including the ones worth nothing.

        A category that vanishes when it is empty makes the band a different
        shape on every address, and a reader cannot learn a legend that moves.
        """
        bands = allocation_bands(Totals(1, 0, 0, 0, 0), {"nft": 0})

        assert [band["key"] for band in bands] == [
            "balance",
            "staked",
            "liquidity",
            "defi",
            "nft",
        ]

    def test_the_nft_figure_comes_from_a_dict(self):
        """`account.total` is a plain dict, not a namedtuple.

        This is a regression test. Both arguments were read with `getattr`,
        which returns the default for every key of a dict -- so the NFT band
        drew 0.00 while the reference address held 1,494.99 ALGO of them, more
        than every other category combined, and the remaining four were shown
        summing to 100%. Nothing errored, and the page looked entirely
        plausible. Found by looking at a screenshot, not by a test.
        """
        bands = allocation_bands(Totals(1, 1, 1, 1, 0), {"nft": 96})

        assert bands[-1]["value"] == 96
        assert bands[-1]["share"] == 96

    def test_the_consolidated_figures_come_from_a_namedtuple(self):
        """The other half of the same asymmetry, pinned so it stays true."""
        bands = allocation_bands(Totals(10, 20, 30, 40, 0), {"nft": 0})

        assert [band["value"] for band in bands[:4]] == [10, 20, 30, 40]

    def test_the_nft_floor_is_not_the_nft_holding(self):
        """`Consolidated`'s last field is the *floor*, and using it under-reports.

        The two are different numbers for the same collections, and the floor is
        the smaller one by construction.
        """
        bands = allocation_bands(Totals(0, 0, 0, 0, 5), {"nft": 100})

        assert bands[-1]["value"] == 100

    def test_shares_sum_to_a_hundred(self):
        """The band is a decomposition and its segments must reach full width.

        A rounding gap at the right-hand end reads as money gone missing.
        """
        bands = allocation_bands(Totals(3, 5, 7, 11, 0), {"nft": 13})

        assert round(sum(band["share"] for band in bands), 6) == 100

    def test_a_debt_contributes_its_size_and_keeps_its_sign(self):
        """A band cannot be drawn a negative width, but it is not nothing.

        Summing signed values would give a total smaller than its parts, and
        shares over 100% -- segments lapping the bar.
        """
        bands = allocation_bands(Totals(75, 0, -25, 0, 0), {"nft": 0})

        assert bands[0]["share"] == 75
        assert bands[2]["share"] == 25
        assert bands[2]["value"] == -25

    def test_an_empty_address_divides_by_nothing(self):
        bands = allocation_bands(Totals(0, 0, 0, 0, 0), {"nft": 0})

        assert [band["share"] for band in bands] == [0, 0, 0, 0, 0]

    def test_an_unevaluated_figure_counts_as_zero(self):
        bands = allocation_bands(Totals("nope", 0, 0, 0, 0), {"nft": 50})

        assert bands[0]["value"] == 0
        assert bands[-1]["share"] == 100

    def test_a_missing_consolidated_yields_nothing(self):
        """Rendering a band of five zeroes would be a claim, not an absence."""
        assert allocation_bands(None, {"nft": 1}) == []

    def test_every_band_names_itself(self):
        bands = allocation_bands(Totals(1, 1, 1, 1, 0), {"nft": 1})

        assert all(band["label"] for band in bands)
