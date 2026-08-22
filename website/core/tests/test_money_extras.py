"""The template filters the money-column designs are built on.

:func:`program_groups` stacks an asset's positions under their program.
:func:`allocation_bands` computes the five categories that the allocation bar,
the five figures and the ratio donut all draw from. :func:`position_band` says
which of those five a single position belongs to, which is what lets the band
act as a filter rather than only report. :func:`holdings_amount` renders the
sort key behind the toolbar's Holdings button.

All four are presentation, which is why they are filters rather than view
context: design 1 renders the same payload ungrouped, and the serialized
payload is shared with the JSON API, which must not grow a website-shaped key.

Two of them restate something computed elsewhere -- `position_band` the
category rule from :mod:`utils.charts`, `holdings_amount` the figure
`amount_repr` displays -- and each has a test here that holds it to the
original against the real payload. That pairing is the condition on restating
anything: a copy nothing compares is a copy that has already drifted.
"""

import json
from collections import namedtuple
from pathlib import Path

import pytest

from core.templatetags.core_extras import (
    allocation_bands,
    amount_repr,
    beats_last_purchase,
    clears_floor,
    collection_above_floor,
    collection_floor,
    collection_tile,
    holdings_amount,
    position_band,
    program_groups,
)

#: Stands in for `utils.structs.Consolidated` without importing the real one,
#: so these tests fail on a field rename rather than following it silently.
Totals = namedtuple("Totals", ["balance", "staked", "liquidity", "defi", "nftfloor"])

#: The captured bundle payload: 76 assets, 190 positions, every position type
#: the engine emits. A hand-built fixture would agree with whatever rule it was
#: written against, which is the one thing the cross-check below must not do.
SAMPLE = (
    Path(__file__).parent.parent.parent / "utils/tests/sample_serialized_540A5.json"
)


@pytest.fixture(scope="module")
def payload():
    """The captured serialized account payload."""
    return json.loads(SAMPLE.read_text())


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


class TestPositionBand:
    """The per-position category the toolbar's filter acts on.

    The band above the list and the list itself have to agree about which
    category a row belongs to, or pressing "Staked" shows a balance row and the
    reader learns the band cannot be trusted. The payload carries no per-
    position category -- ``Consolidated`` arrives already summed -- so
    :func:`position_band` reproduces the rule, and :class:`TestPositionBandMatchesConsolidated`
    is what stops the reproduction drifting.
    """

    def test_a_wallet_balance_is_balance(self):
        assert position_band(_program("", 1, type_="Balance")) == "balance"

    def test_a_stake_is_staked(self):
        assert position_band(_program("CompX", 1, type_="Staked")) == "staked"

    def test_a_farm_is_not_a_stake(self):
        """`"farm" not in name` is the original rule, substring and all.

        A farm is a yield position rather than a plain stake, and the four
        comprehensions in `utils.charts` sort it into DeFi. Reproduced exactly,
        including the substring match -- tightening it to a word boundary here
        would be a *better* rule and a wrong one, because the band would still
        use the old one.
        """
        assert position_band(_program("AlgoRai farm", 1, type_="Staked")) == "defi"

    def test_added_liquidity_is_liquidity(self):
        assert position_band(_program("Liquidity", 1, type_="Added")) == "liquidity"

    def test_added_something_else_is_defi(self):
        """`type == "Added"` alone is not enough; the name decides."""
        assert position_band(_program("Collateral", 1, type_="Added")) == "defi"

    def test_anything_unrecognised_is_defi(self):
        """The catch-all, matching the original's `if not (...)` shape.

        A position type nobody has seen yet still belongs in the picture, and
        DeFi is where the original puts it.
        """
        assert position_band(_program("Folks", 1, type_="Borrowed")) == "defi"

    def test_a_position_with_no_program_detail_is_defi(self):
        """Not a crash, and not silently dropped from the band."""
        assert position_band({}) == "defi"
        assert position_band(None) == "defi"
        assert position_band({"program": None}) == "defi"


@pytest.mark.parametrize(
    "band, field",
    [("balance", "balance"), ("staked", "staked"), ("liquidity", "liquidity"), ("defi", "defi")],
)
def test_position_band_agrees_with_consolidated(payload, band, field):
    """Sum the real payload by category and compare against `Consolidated`.

    This is the test that makes reproducing the rule acceptable. `utils.charts`
    computes each category as a dict comprehension over the whole payload, with
    no per-position function to share; :func:`position_band` says the same
    thing one position at a time. If either side changes, these totals part
    company and this fails -- which is the only reason the duplication is safe
    to have.
    """
    from utils.charts import _consolidated_data_from_serialized_data
    from utils.charts import _consolidated_totals_from_consolidated_data

    totals = _consolidated_totals_from_consolidated_data(
        _consolidated_data_from_serialized_data(payload)
    )

    summed = sum(
        float(program.get("value") or 0)
        for item in payload["asaitems"]
        for program in (item.get("programs") or [])
        if position_band(program) == band
    )

    assert round(summed, 6) == round(float(getattr(totals, field)), 6)


class TestHoldingsAmount:
    """The sort key behind the toolbar's Holdings button.

    A number the browser can read, in the asset's own units. Every case here is
    a shape the reference payload actually contains -- 6-decimal assets, a
    0-decimal Lofty share, an asset holding nothing -- plus the two ways the
    payload can be malformed.
    """

    def test_it_shifts_the_amount_by_the_decimals(self):
        assert (
            holdings_amount({"amount": 169514449, "asset": {"decimals": 6}})
            == "169.514449"
        )

    def test_a_zero_decimal_asset_keeps_its_whole_count(self):
        """Lofty shares are held one at a time and have no decimal places."""
        assert holdings_amount({"amount": 1, "asset": {"decimals": 0}}) == "1.0"

    def test_the_number_is_never_grouped(self):
        """The whole reason this exists rather than parsing `amount_repr`.

        That filter renders "123,456,789.012345" for reading, and a browser
        parsing it back would have to agree with Django's thousands separator
        forever -- which is locale-dependent, so the agreement is not one this
        code can make on its own behalf.
        """
        rendered = holdings_amount({"amount": 123456789012345, "asset": {"decimals": 6}})

        assert rendered == "123456789.012345"
        assert "," not in rendered

    def test_raw_amount_is_not_what_is_emitted(self):
        """Two assets holding "one" must not sort a million places apart.

        `amount` is in the asset's base units, so an asset with 6 decimals
        holding one unit carries 1000000 and a 0-decimal asset holding one
        carries 1. Sorting on the raw figure ranks by decimal places.
        """
        six = holdings_amount({"amount": 1000000, "asset": {"decimals": 6}})
        none = holdings_amount({"amount": 1, "asset": {"decimals": 0}})

        assert float(six) == float(none) == 1.0

    def test_an_asset_holding_nothing_is_zero(self):
        assert float(holdings_amount({"amount": 0, "asset": {"decimals": 6}})) == 0.0

    def test_a_missing_amount_is_zero(self):
        assert float(holdings_amount({"asset": {"decimals": 6}})) == 0.0

    def test_a_missing_decimals_shifts_by_nothing(self):
        """Rather than dropping the row out of the sort entirely."""
        assert holdings_amount({"amount": 42, "asset": {}}) == "42.0"

    def test_a_missing_asset_shifts_by_nothing(self):
        assert holdings_amount({"amount": 42}) == "42.0"

    def test_decimals_arriving_as_a_string_still_counts(self):
        """The payload is JSON from another service; it is not ours to trust."""
        assert holdings_amount({"amount": 500, "asset": {"decimals": "2"}}) == "5.0"

    @pytest.mark.parametrize(
        "asaitem",
        [
            {"amount": "not a number", "asset": {"decimals": 6}},
            {"amount": 1, "asset": {"decimals": "six"}},
            "not an asaitem",
            None,
            42,
        ],
        ids=["bad amount", "bad decimals", "a string", "None", "a number"],
    )
    def test_anything_unusable_sorts_as_zero(self, asaitem):
        """Never an exception.

        This renders into an attribute on every row of the busiest page on the
        site. A row the payload cannot describe sorts to one end; it does not
        take the page down with it.
        """
        assert holdings_amount(asaitem) == "0"

    def test_a_holding_too_small_for_plain_notation_is_still_a_number(self):
        """Algorand allows 19 decimal places, and `repr` switches to `1e-19`.

        Left as it is rather than formatted: `parseFloat` reads exponent
        notation exactly, and forcing plain decimals would mean choosing a
        precision -- which is how a holding becomes 0 in a sort.
        """
        rendered = holdings_amount({"amount": 1, "asset": {"decimals": 19}})

        assert rendered == "1e-19"
        assert float(rendered) > 0

    def test_it_agrees_with_what_the_row_displays(self, payload):
        """The sort key and the visible holding are the same number.

        `amount_repr` renders the figure a reader sees and this renders the one
        the browser sorts on. They are computed separately, so nothing but a
        test stops them drifting -- and a Holdings sort that disagreed with the
        column it claims to sort would be silently, unfalsifiably wrong.
        """
        checked = 0
        for item in payload["asaitems"]:
            decimals = item["asset"].get("decimals") or 0
            displayed = amount_repr(item.get("amount"), decimals)
            sorted_on = holdings_amount(item)

            # `amount_repr` rounds to the asset's decimals and groups; compare
            # as numbers, which is what both are for.
            assert float(sorted_on) == pytest.approx(
                float(displayed.replace(",", "")), rel=1e-9
            ), f"{item['asset'].get('unit')}: shows {displayed}, sorts on {sorted_on}"
            checked += 1

        assert checked > 50, "too few assets to prove anything"


def _item(price, floor=None, last=None, best=None):
    """Build one entry of a collection's ``nfts`` list."""
    nft = {}
    if floor is not None:
        nft["floor"] = [{"price": floor, "market": {"name": "Asalytic"}}]
    if last is not None:
        nft["last_purchase"] = {"price": last, "market": {"name": "Rand Gallery"}}
    if best is not None:
        nft["max_purchase"] = {"price": best, "market": {"name": "Rand Gallery"}}
    return {"price": price, "value": price, "amount": 1, "nft": nft}


class TestCollectionFloor:
    """What a marketplace will pay for a collection today.

    The estimate is what the section totals; the floor is the other number, and
    the gap between them is the only thing about a collection that one figure
    cannot say.
    """

    def test_it_sums_the_items_floors(self):
        collection = {"value": "300", "nfts": [_item("200", floor="25"), _item("100", floor="30")]}

        assert collection_floor(collection) == 55.0

    def test_an_item_nobody_floors_contributes_nothing(self):
        """A floor of zero and no floor at all are the same amount of money.

        Which of the two it is gets said by a chip beside the name, not by the
        number -- so the number does not have to carry it.
        """
        collection = {"value": "300", "nfts": [_item("200", floor="25"), _item("100")]}

        assert collection_floor(collection) == 25.0

    def test_only_the_first_marketplace_counts(self):
        """An item can be floored on several, and design 1 reports the first.

        Differing on which floor is "the" floor would be a worse divergence
        between the two designs than either choice is on its own.
        """
        collection = {
            "value": "300",
            "nfts": [
                {
                    "price": "200",
                    "nft": {
                        "floor": [
                            {"price": "25", "market": {"name": "Asalytic"}},
                            {"price": "40", "market": {"name": "Rand"}},
                        ]
                    },
                }
            ],
        }

        assert collection_floor(collection) == 25.0

    def test_a_collection_with_no_items_floors_at_nothing(self):
        assert collection_floor({"value": "0", "nfts": []}) == 0.0

    @pytest.mark.parametrize("collection", [None, {}, {"nfts": None}], ids=["None", "empty", "null nfts"])
    def test_a_collection_the_payload_did_not_describe(self, collection):
        assert collection_floor(collection) == 0.0


class TestCollectionAboveFloor:
    """The second half of the two-part bar."""

    def test_it_is_what_the_estimate_adds_to_the_floor(self):
        collection = {"value": "100", "nfts": [_item("100", floor="30")]}

        assert collection_above_floor(collection) == pytest.approx(70.0)

    def test_an_estimate_below_the_floor_does_not_draw_backwards(self):
        """A negative flex basis would either be ignored or invert the bar.

        The reading a reader would take from an inverted bar -- mostly floor,
        a sliver of hope -- is the opposite of what it means.
        """
        collection = {"value": "10", "nfts": [_item("10", floor="30")]}

        assert collection_above_floor(collection) == 0.001

    def test_an_estimate_exactly_at_the_floor_still_draws(self):
        """A flex basis of zero collapses the *whole* bar, not one side of it."""
        collection = {"value": "30", "nfts": [_item("30", floor="30")]}

        assert collection_above_floor(collection) == 0.001


class TestClearsFloor:
    """Whether an item's estimate reaches the floor it is priced against."""

    def test_an_estimate_above_the_floor_clears_it(self):
        assert clears_floor(_item("215.98", floor="25.00")) is True

    def test_an_estimate_below_the_floor_does_not(self):
        assert clears_floor(_item("10.00", floor="25.00")) is False

    def test_an_estimate_exactly_at_the_floor_clears_it(self):
        assert clears_floor(_item("25.00", floor="25.00")) is True

    def test_the_comparison_is_numeric_rather_than_lexical(self):
        """The reason this is a filter at all.

        Both figures are decimal strings, and `{% if a > b %}` compares those
        character by character: "215.98" sorts below "25.00", so an item worth
        eight times its floor would have been reported as not clearing it. Every
        item on the reference address with a three-figure estimate hits this.
        """
        assert "215.98" < "25.00"
        assert clears_floor(_item("215.98", floor="25.00")) is True

    def test_an_item_with_no_floor_clears_nothing(self):
        """The template renders a different line for that case."""
        assert clears_floor(_item("215.98")) is False

    @pytest.mark.parametrize("row", [None, {}, {"nft": None}], ids=["None", "empty", "null nft"])
    def test_an_item_the_payload_did_not_describe(self, row):
        assert clears_floor(row) is False


class TestBeatsLastPurchase:
    """Whether the best price paid for an item beats the most recent one."""

    def test_a_higher_best_price_beats_it(self):
        assert beats_last_purchase(_item("1", last="10", best="99")["nft"]) is True

    def test_the_same_transaction_twice_does_not(self):
        """Which is what the reference address shows for most items."""
        assert beats_last_purchase(_item("1", last="210", best="210")["nft"]) is False

    def test_the_comparison_is_numeric_rather_than_lexical(self):
        assert "9.5" > "210.0"
        assert beats_last_purchase(_item("1", last="210.0", best="9.5")["nft"]) is False

    def test_an_item_never_bought_has_nothing_to_beat(self):
        assert beats_last_purchase(_item("1")["nft"]) is False

    def test_a_best_price_with_no_last_purchase_still_beats(self):
        """The pair usually arrives together; one without the other is news."""
        assert beats_last_purchase(_item("1", best="10")["nft"]) is True

    @pytest.mark.parametrize("nft", [None, {}], ids=["None", "empty"])
    def test_an_item_the_payload_did_not_describe(self, nft):
        assert beats_last_purchase(nft) is False


class TestCollectionTile:
    """The short label on a collection's tile.

    A collection has no logo, so the tile carries initials. Four characters is
    what fits the 38px tile at the prototype's type size; longer names are cut
    rather than scaled, because shrinking the type to fit makes some tiles
    unreadable and the rest inconsistent.
    """

    def test_a_multi_word_name_gives_its_initials(self):
        assert collection_tile("Brave New World") == "BNW"

    def test_a_single_word_gives_its_leading_characters(self):
        assert collection_tile("knitH3Ds") == "KNIT"

    def test_a_long_name_is_cut_rather_than_scaled(self):
        assert collection_tile("Waking in Costa Rica, part two") == "WICR"

    def test_a_short_name_is_left_alone(self):
        assert collection_tile("AB") == "AB"

    @pytest.mark.parametrize("name", ["", "   ", None], ids=["empty", "spaces", "None"])
    def test_a_collection_with_no_name_still_gets_a_tile(self, name):
        """An empty tile reads as a rendering fault rather than as missing data."""
        assert collection_tile(name) == "?"

    def test_it_agrees_with_the_real_collections(self, payload):
        """Every collection on the reference address gets a usable tile."""
        tiles = [collection_tile(coll["name"]) for coll in payload["nftcollections"]]

        assert len(tiles) > 50
        assert all(1 <= len(tile) <= 4 for tile in tiles), [
            tile for tile in tiles if len(tile) > 4
        ]
        assert all(tile == tile.upper() for tile in tiles)


def test_collection_floor_and_estimate_agree_with_the_payload(payload):
    """The two halves of the bar add up to the collection's own value.

    Computed separately -- one sums the items' floors, the other subtracts that
    from the collection's estimate -- so nothing but this stops them drifting
    into a bar that does not describe the collection it sits under.
    """
    checked = 0
    for collection in payload["nftcollections"]:
        floor = collection_floor(collection)
        above = collection_above_floor(collection)
        estimate = float(collection["value"])

        # The 0.001 floor on the second half shows up on collections whose
        # estimate does not clear their floor; those are the ones it exists for.
        if estimate >= floor:
            assert floor + above == pytest.approx(estimate, abs=0.002), collection["name"]
        checked += 1

    assert checked > 50
