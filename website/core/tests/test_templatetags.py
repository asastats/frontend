"""Testing module for core app's template tags and filters."""

import pytest
from django.conf import settings

from core.templatetags.core_extras import (
    abs_value,
    amount_repr,
    asa_icon,
    beyond,
    bundle_hash,
    dict_get,
    dist_height,
    dist_price,
    explorer_base,
    explorer_name,
    explorer_tx_path,
    explorer_url,
    get_styling,
    has_styling,
    historic_access,
    historic_data,
    integer_comma,
    invert_price,
    is_distribution,
    is_negative,
    list_item,
    next_batch,
    program_url,
    program_url_title,
    provider_icon,
    short_address,
    short_addresses,
    split_by_space,
    strid,
)
from utils.tests.fixtures import (
    TEST_ADDRESS,
    TEST_ADDRESS2,
    TEST_ADDRESS3,
    TESTING_ASAS,
    TESTING_VALUES,
)


class TestFilters:
    # # asa_icon
    def _asaitem(self, asset_id=505, name="", unit="", programs=None):
        return {
            "asset": {"id": asset_id, "name": name, "unit": unit},
            "programs": programs or [],
        }

    def test_filters_asa_icon_returns_lofty_icon_for_lofty_provider(self):
        # Explicit Lofty provider on any program → Lofty badge.
        item = self._asaitem(
            asset_id=505,
            programs=[{"program": {"provider": {"name": "Lofty"}}}],
        )
        assert asa_icon(item) == settings.BASE_CDN_URL + "/icons/providers/lofty.png"

    def test_filters_asa_icon_returns_lofty_icon_for_lofty_asset_name(self):
        item = self._asaitem(asset_id=505, name="Lofty 3878 Windermere Rd")
        assert asa_icon(item) == settings.BASE_CDN_URL + "/icons/providers/lofty.png"

    def test_filters_asa_icon_returns_lofty_icon_for_lofty_linked_url(self):
        # Third signal: any program's linked URL contains "lofty".
        item = self._asaitem(
            asset_id=505,
            programs=[
                {
                    "program": {"type": "Balance"},
                    "linked": [{"link": "https://www.lofty.ai/property_deal/X"}],
                }
            ],
        )
        assert asa_icon(item) == settings.BASE_CDN_URL + "/icons/providers/lofty.png"

    def test_filters_asa_icon_returns_usdc_icon_for_lofty_signals_and_usdc(self):
        # USDC is hard-excluded from the override; it's the quote currency
        # and never carries meaningful provider semantics.
        item = self._asaitem(
            asset_id=31566704,
            unit="USDC",
            programs=[{"program": {"provider": {"name": "Lofty"}}}],
        )
        assert asa_icon(item) == settings.BASE_CDN_URL + "/icons/31566704t.png"

    def test_filters_asa_icon_returns_anote_icon_for_anote_provider(self):
        item = self._asaitem(
            asset_id=505,
            programs=[{"program": {"provider": {"name": "ANote"}}}],
        )
        assert asa_icon(item) == settings.BASE_CDN_URL + "/icons/providers/anote.png"

    def test_filters_asa_icon_returns_anote_icon_for_anmc_unit_prefix(self):
        # ANote music tokens use the anmc unit prefix; their asset names
        # vary per release so the unit prefix is the reliable signal.
        item = self._asaitem(asset_id=505, unit="anmc1")
        assert asa_icon(item) == settings.BASE_CDN_URL + "/icons/providers/anote.png"

    def test_filters_asa_icon_returns_image_path(self):
        # No override signals — fall back to the standard thumbnail path.
        item = self._asaitem(asset_id=226701642, name="Yieldly", unit="YLDY")
        assert asa_icon(item) == settings.BASE_CDN_URL + "/icons/226701642t.png"

    # # bundle_hash
    @pytest.mark.parametrize(
        "collection,result",
        [
            ([TEST_ADDRESS, TEST_ADDRESS2], "65B4307A047B8276EEA9F184EE78975A5F47ACA1"),
            (
                [
                    TEST_ADDRESS,
                    TEST_ADDRESS,
                    TEST_ADDRESS2,
                ],
                "65B4307A047B8276EEA9F184EE78975A5F47ACA1",
            ),
            ([TEST_ADDRESS, TEST_ADDRESS3], "8C6405F9FC1E9CD5078C4B0CEA15C7CBCF484800"),
            (
                [TEST_ADDRESS2, TEST_ADDRESS3],
                "540A5D8CEC896E073F9170AF0A962503E69147CF",
            ),
            (
                [TEST_ADDRESS, TEST_ADDRESS2, TEST_ADDRESS3],
                "8F509823948F7595D6138602C80E5DF8CAFD3A70",
            ),
        ],
    )
    def test_filters_bundle_hash_functionality(self, collection, result):
        assert bundle_hash(collection) == result

    # # dict_get
    # Renamed from dict_value with a defensive ``None`` handler so that
    # missing colors= contexts don't crash templates.
    def test_filters_dict_get_returns_value(self):
        assert dict_get({"bar": 1}, "bar") == 1

    def test_filters_dict_get_returns_empty_string_for_invalid_key(self):
        assert dict_get({"bar": 1}, "foo") == ""

    def test_filters_dict_get_returns_empty_string_for_none_mapping(self):
        # Templates may pass colors=None if a view forgets to wire it up;
        # we degrade to no-color rather than raising AttributeError.
        assert dict_get(None, "foo") == ""

    def test_filters_dict_get_works_with_integer_keys(self):
        # Colors are keyed by asset id (int). Django's dotted lookup
        # syntax can't index dicts with int keys, which is the whole
        # reason this filter exists.
        assert dict_get({0: "algo", 31566704: "0"}, 31566704) == "0"

    # # dist_height
    @pytest.mark.parametrize(
        "distchart,result",
        [
            ({}, 80),
            ({"labels": []}, 80),
            ({"labels": [1]}, 80),
            ({"labels": [1, 2]}, 106),
            ({"labels": [1, 2, 3]}, 132),
            ({"labels": [1, 2, 3, 4]}, 159),
            ({"labels": [1, 2, 3, 4, 5]}, 185),
            ({"labels": [1] * 15}, 475),
            ({"labels": [1] * 16}, 475),
            ({"labels": [1] * 20}, 475),
        ],
    )
    def test_filters_dist_height_functionality(self, distchart, result):
        assert dist_height(distchart) == result

    # # historic_access
    def test_filters_historic_access_for_no_profile(self):
        profile = None
        returned = historic_access(profile, 5)
        assert returned is False

    def test_filters_historic_access_functionality(self, mocker):
        profile = mocker.MagicMock()
        size = 5
        returned = historic_access(profile, size)
        assert returned == profile.can_access_historic_widget.return_value
        profile.can_access_historic_widget.assert_called_once_with(size)

    # # historic_data
    def test_filters_historic_data_for_bundle(self):
        bundle = [TEST_ADDRESS, TEST_ADDRESS2, TEST_ADDRESS3]
        returned = historic_data(bundle)
        assert returned == ("8F509823948F7595D6138602C80E5DF8CAFD3A70", 3)

    # # integer_comma
    @pytest.mark.parametrize(
        "value,result",
        [
            (0, "0"),
            (1000, "1,000"),
            (999000, "999,000"),
            (9000999000999000, "9,000,999,000,999,000"),
        ],
    )
    def test_filters_integer_comma_returns_formatted_value(self, value, result):
        assert integer_comma(value) == result

    # # list_item
    def test_filters_list_item_returns_value(self):
        assert list_item([1, 2, 3], 2) == 3

    def test_filters_list_item_returns_empty_string_for_invalid_index(self):
        assert list_item([1, 2, 3], 3) == ""

    # # amount_repr
    #
    # Four decimal places at most, which is what the Materialize design showed
    # and what the rebuild keeps. Indexes 0, 2 and 3 are the ones that used to
    # print the asset's full precision -- six, five and ten places.
    @pytest.mark.parametrize(
        "index,result",
        [
            (0, "26,872.2838"),
            (1, "355,029"),
            (2, "10,000.0010"),
            (3, "3.0000"),
            (4, "5,140"),
            (5, "300"),
            (6, "625"),
            (7, "20"),
            (8, "700"),
            (9, "1"),
        ],
    )
    def test_filters_amount_repr_returns_calculated_value(self, index, result):
        asset = TESTING_VALUES[index]
        decimals = TESTING_ASAS[asset[1]].decimals
        returned = amount_repr(asset[2], decimals)
        assert returned == result

    def test_filters_amount_repr_returns_zero_for_valueerror(self):
        returned = amount_repr(5, ())
        assert returned == "0"

    @pytest.mark.parametrize(
        "amount,decimals,result",
        [
            # an asset declaring fewer than the cap keeps its own precision
            (12345, 2, "123.45"),
            (700000, 3, "700"),
            # and one declaring more is cut to the cap, not to its own
            (26872283825, 6, "26,872.2838"),
            (30000000010, 10, "3.0000"),
            # exactly at the cap, unchanged
            (1234567, 4, "123.4567"),
            # no decimals at all is an integer, not "1.0000"
            (355029, 0, "355,029"),
        ],
    )
    def test_filters_amount_repr_shows_at_most_four_decimals(
        self, amount, decimals, result
    ):
        """The cap is on display only; the division keeps the real decimals.

        `10,000.0010` rather than `10,000.001` is Django's `-N`, which means
        "N places unless the value is whole" rather than "strip trailing
        zeros". Pinned because it looks like a bug and is not.
        """
        assert amount_repr(amount, decimals) == result

    def test_filters_amount_repr_divides_by_the_assets_decimals_not_the_cap(self):
        """The one way this could be wrong and still look plausible.

        Capping the divisor instead of the display would turn 26,872.283825
        into 2,687,228.3825 -- a holding a hundred times too large, rendered
        with a confident four decimal places.
        """
        assert amount_repr(26872283825, 6).startswith("26,872")

    def test_filters_amount_repr_survives_a_negative_decimals(self):
        """`max(..., 0)` guards a format string that would otherwise be "--3g".

        `floatformat` returns the value untouched for an unparsable argument
        rather than raising, so without the guard this is a silently wrong
        number instead of the "0" every other bad input gets.
        """
        assert amount_repr(250, -1) == "2,500"

    # # is_distribution
    def test_filters_is_distribution_returns_true(self):
        assert is_distribution("XET-XET")

    def test_filters_is_distribution_returns_false(self):
        assert not is_distribution("YLDY-XET")

    def test_filters_is_distribution_returns_false_for_name_without_dash(self):
        assert not is_distribution("FOOBAR")

    # # short_address
    def test_filters_short_address_returns_string(self):
        assert (
            short_address(TEST_ADDRESS) == TEST_ADDRESS[:5] + "..." + TEST_ADDRESS[-5:]
        )

    # # short_addresses
    def test_filters_short_addresses_returns_string(self):
        assert (
            short_addresses(f"{TEST_ADDRESS3} {TEST_ADDRESS} {TEST_ADDRESS2}")
            == TEST_ADDRESS3[:5]
            + "..."
            + TEST_ADDRESS3[-5:]
            + "\n"
            + TEST_ADDRESS[:5]
            + "..."
            + TEST_ADDRESS[-5:]
            + "\n"
            + TEST_ADDRESS2[:5]
            + "..."
            + TEST_ADDRESS2[-5:]
        )

    # # split_by_space
    def test_filters_split_by_space_returns_addresses(self):
        assert split_by_space(f"{TEST_ADDRESS3} {TEST_ADDRESS} {TEST_ADDRESS2}") == [
            TEST_ADDRESS3,
            TEST_ADDRESS,
            TEST_ADDRESS2,
        ]

    # # strid
    def test_filters_strid_returns_concatenated_value(self):
        prefix = "prefix"
        number = 505
        returned = strid(prefix, number)
        assert returned == "{}{}".format(prefix, number)

    # # get_styling
    def test_filters_get_styling_returns_value_if_valid_key_supplied(self):
        assert get_styling("login", "icon") == "account_circle"

    def test_filters_get_styling_returns_empty_string_if_invalid_elem_supplied(self):
        assert get_styling("foo", "icon") == ""

    def test_filters_get_styling_returns_empty_string_if_invalid_key_supplied(self):
        assert get_styling("login", "foo") == ""

    # # has_styling
    def test_filters_has_styling_returns_false_if_there_is_not_such_element(self):
        assert not has_styling("foo")

    def test_filters_has_styling_returns_true_if_there_is_element(self):
        assert has_styling("login")

    # # provider_icon
    # The filter converts a Provider.name to the icon-filename convention
    # used under the CDN's icons/providers/: lowercase, whitespace stripped,
    # no dashes. Matches the existing file naming (livecoinwatch.png,
    # coinmarketcap.png, etc.) rather than Django's |slugify which would
    # produce live-coin-watch.png and break the icon path.
    @pytest.mark.parametrize(
        "name,result",
        [
            ("Vestige", "icons/providers/vestige.png"),
            ("Haystack", "icons/providers/haystack.png"),
            ("CoinMarketCap", "icons/providers/coinmarketcap.png"),
            ("Live Coin Watch", "icons/providers/livecoinwatch.png"),
            ("DEX Screener", "icons/providers/dexscreener.png"),
            ("Lofty", "icons/providers/lofty.png"),
            ("ANote", "icons/providers/anote.png"),
        ],
    )
    def test_filters_provider_icon_returns_slugified_path(self, name, result):
        assert provider_icon(name) == settings.BASE_CDN_URL + "/" + result

    def test_filters_provider_icon_returns_empty_string_for_empty_input(self):
        # Defensive: passing the result into {% static %} would crash on an
        # empty path, so return "" and let the template's {% if %} skip it.
        assert provider_icon("") == ""

    def test_filters_provider_icon_returns_empty_string_for_none_input(self):
        assert provider_icon(None) == ""

    # # program_url_title
    # The filter centralises the "Go to <provider> application" anchor
    # title text that the legacy templates inlined into every per-key
    # branch. Falls back through provider name → program name → generic.
    def test_filters_program_url_title_uses_provider_name(self):
        program = {"provider": {"name": "Tinyman2 LP"}, "name": "Liquidity"}
        assert program_url_title(program) == "Go to Tinyman2 LP application"

    def test_filters_program_url_title_falls_back_to_program_name(self):
        # Some programs only have a name, no provider.
        program = {"name": "Algorand Foundation Governance"}
        assert (
            program_url_title(program)
            == "Go to Algorand Foundation Governance application"
        )

    def test_filters_program_url_title_final_fallback(self):
        # Neither name nor provider — emit a generic title rather than
        # the literal string "Go to  application" with double spaces.
        assert program_url_title({}) == "Go to provider application"

    def test_filters_program_url_title_handles_none_program(self):
        # Defensive: an upstream partial may pass prog.program as None
        # for a malformed serializer output.
        assert program_url_title(None) == "Go to provider application"


class TestFiltersInvertPrice:
    """Tests for the invert_price filter (Phase 5c-fixes / W3)."""

    def test_filters_invert_price_returns_reciprocal_for_positive_float(self):
        # The canonical case from the issue report: USDC's price is
        # ~9.118769 ALGO/USDC; the inverted form (USDC/ALGO) is ~0.10966.
        assert invert_price(9.118769008220958) == pytest.approx(0.10966392, abs=1e-7)

    def test_filters_invert_price_handles_string_input(self):
        # Django templates often pass values through as strings (Decimal
        # fields serialize to "9.118769" by default).
        assert invert_price("9.118769008220958") == pytest.approx(0.10966392, abs=1e-7)

    def test_filters_invert_price_returns_zero_for_none(self):
        assert invert_price(None) == 0.0

    def test_filters_invert_price_returns_zero_for_zero(self):
        assert invert_price(0) == 0.0
        assert invert_price("0") == 0.0
        assert invert_price(0.0) == 0.0

    def test_filters_invert_price_returns_zero_for_empty_string(self):
        # `not price` truthiness check catches empty strings.
        assert invert_price("") == 0.0

    def test_filters_invert_price_returns_zero_for_garbage(self):
        # Non-numeric strings (shouldn't happen for a real price field
        # but the filter is defensive).
        assert invert_price("not a number") == 0.0
        assert invert_price([1, 2, 3]) == 0.0


class TestFiltersIsNegative:
    """Tests for the is_negative filter (Phase 5c-fixes / W7)."""

    def test_filters_is_negative_returns_true_for_negative_string(self):
        # Canonical case from the Folks borrow example.
        assert is_negative("-0.003470") is True

    def test_filters_is_negative_returns_true_for_negative_int(self):
        assert is_negative(-10092956) is True

    def test_filters_is_negative_returns_true_for_negative_float(self):
        assert is_negative(-0.5) is True

    def test_filters_is_negative_returns_false_for_zero(self):
        # Zero is not "negative" — borrow detection must skip empties.
        assert is_negative(0) is False
        assert is_negative("0") is False
        assert is_negative(0.0) is False

    def test_filters_is_negative_returns_false_for_positive(self):
        assert is_negative(5) is False
        assert is_negative("0.5") is False
        assert is_negative(0.5) is False

    def test_filters_is_negative_returns_false_for_none(self):
        assert is_negative(None) is False

    def test_filters_is_negative_returns_false_for_garbage(self):
        assert is_negative("not a number") is False
        assert is_negative([]) is False


class TestFiltersAbsValue:
    """Tests for the abs_value filter (Phase 5c-fixes / W7)."""

    def test_filters_abs_value_returns_int_for_int_input(self):
        # ``amount_repr`` expects ``int(amount) / 10**decimals``, so the
        # filter must preserve int-ness to compose correctly.
        result = abs_value(-10092956)
        assert result == 10092956
        assert isinstance(result, int)

    def test_filters_abs_value_returns_float_for_string_input(self):
        result = abs_value("-0.003470")
        assert result == pytest.approx(0.003470, abs=1e-7)
        assert isinstance(result, float)

    def test_filters_abs_value_returns_float_for_float_input(self):
        result = abs_value(-0.5)
        assert result == 0.5
        assert isinstance(result, float)

    def test_filters_abs_value_passes_through_positive(self):
        assert abs_value(5) == 5
        assert abs_value(0.5) == 0.5

    def test_filters_abs_value_returns_zero_for_zero(self):
        assert abs_value(0) == 0

    def test_filters_abs_value_returns_zero_for_none(self):
        assert abs_value(None) == 0

    def test_filters_abs_value_returns_zero_for_garbage(self):
        assert abs_value("not a number") == 0
        assert abs_value([]) == 0

    def test_filters_abs_value_composes_with_amount_repr(self):
        # The realistic pipeline: prog.amount (negative int) -> abs_value
        # -> amount_repr -> displayed string. Verify the chain works end
        # to end for the Folks borrow example.
        result = amount_repr(abs_value(-10092956), 6)
        # 10092956 / 1e6 = 10.092956, shown to the four-place cap. What this
        # test is really for is the sign: the magnitude survives abs_value and
        # the parentheses in the template carry the "borrowed" meaning.
        assert result == "10.0930"
        assert "-" not in result


class TestFiltersDistPrice:
    """Tests for the dist_price tag (Phase 5c-fixes / distribution
    price bug: rows were all rendering the parent asaitem's top-level
    `price` instead of a per-entry price)."""

    # Canonical fixtures, taken verbatim from the ASASTATS address-page
    # bug report. asset.decimals == 6 (confirmed against the page's
    # displayed Balance: 50,685,747.637078 == 50685747637078 / 1e6).

    def test_dist_price_returns_correct_value_for_pact_swap(self):
        d = {"value": "3693.630910", "amount": 31447473319470}
        assert dist_price(d, 6) == pytest.approx(0.00011745398024435785)

    def test_dist_price_returns_correct_value_for_tinyman_swap(self):
        d = {"value": "1779.032425", "amount": 15146055670400}
        assert dist_price(d, 6) == pytest.approx(0.00011745846335932666)

    def test_dist_price_returns_correct_value_for_pact_pow_swap(self):
        d = {"value": "480.701171", "amount": 4092218647207}
        assert dist_price(d, 6) == pytest.approx(0.00011746712784471712)

    def test_dist_price_differs_across_distribution_entries(self):
        # Regression test for the actual bug: three distinct entries
        # must not collapse to the same price.
        pact = dist_price({"value": "3693.630910", "amount": 31447473319470}, 6)
        tinyman = dist_price({"value": "1779.032425", "amount": 15146055670400}, 6)
        pact_pow = dist_price({"value": "480.701171", "amount": 4092218647207}, 6)
        assert len({pact, tinyman, pact_pow}) == 3

    def test_dist_price_returns_none_for_zero_amount(self):
        d = {"value": "100.0", "amount": 0}
        assert dist_price(d, 6) is None

    def test_dist_price_returns_none_for_missing_amount_key(self):
        d = {"value": "100.0"}
        assert dist_price(d, 6) is None

    def test_dist_price_returns_none_for_missing_value_key(self):
        d = {"amount": 31447473319470}
        assert dist_price(d, 6) is None

    def test_dist_price_returns_none_for_none_dict(self):
        assert dist_price(None, 6) is None

    def test_dist_price_returns_none_for_garbage_value(self):
        d = {"value": "not a number", "amount": 31447473319470}
        assert dist_price(d, 6) is None

    def test_dist_price_returns_none_for_garbage_amount(self):
        d = {"value": "3693.630910", "amount": "not a number"}
        assert dist_price(d, 6) is None

    def test_dist_price_returns_none_for_garbage_decimals(self):
        d = {"value": "3693.630910", "amount": 31447473319470}
        assert dist_price(d, "not a number") is None

    def test_dist_price_returns_none_for_negative_amount_that_is_zero_units(self):
        # Extreme edge: amount so small relative to decimals it can't
        # be zero here, but decimals=0 with amount=0 should still
        # short-circuit to None rather than raise.
        d = {"value": "5.0", "amount": 0}
        assert dist_price(d, 0) is None

    def test_dist_price_accepts_string_decimals(self):
        # asset.decimals sometimes arrives as a string from template
        # context; must not raise.
        d = {"value": "3693.630910", "amount": 31447473319470}
        assert dist_price(d, "6") == pytest.approx(0.00011745398024435785)

    def test_dist_price_accepts_int_and_float_value_types(self):
        d_str = {"value": "3693.630910", "amount": 31447473319470}
        d_float = {"value": 3693.630910, "amount": 31447473319470}
        assert dist_price(d_str, 6) == pytest.approx(dist_price(d_float, 6))

    def test_dist_price_handles_zero_decimals(self):
        d = {"value": "10.0", "amount": 5}
        assert dist_price(d, 0) == pytest.approx(2.0)

    def test_dist_price_returns_none_for_missing_amount_and_value(self):
        assert dist_price({}, 6) is None

    # -- Balance-row regression (program.html Balance branch reused the
    #    stale top-level oracle `price` instead of computing prog.value /
    #    prog.amount, same as the distribution rows already fixed above.)

    def test_dist_price_on_program_dict_uses_its_own_value_and_amount(self):
        # `prog` carries the same {value, amount} shape as a distribution
        # entry, so dist_price works on it unmodified once called with
        # `prog` instead of `d` in the Balance branch of program.html.
        prog = {"value": "5954.248655", "amount": 50685747637078}
        assert dist_price(prog, 6) == pytest.approx(0.00011747382513983686)

    def test_dist_price_on_program_dict_does_not_equal_stale_oracle_price(self):
        # Regression guard: previously the template displayed the
        # top-level asaitem price (0.000136) for this row regardless of
        # the program's actual value/amount ratio.
        prog = {"value": "5954.248655", "amount": 50685747637078}
        result = dist_price(prog, 6)
        assert result != pytest.approx(0.000136, rel=1e-3)

    def test_dist_price_on_program_dict_is_consistent_with_its_distribution_rows(self):
        # When a Balance program's full amount flows through its own
        # distribution, the program-level implied price should land
        # close to each distribution row's implied price now that both
        # are computed the same way (within float/rounding tolerance,
        # not bit-identical).
        prog = {"value": "5954.248655", "amount": 50685747637078}
        dist_entries = [
            {"value": "3696.460588", "amount": 31466294379687},
            {"value": "1777.572868", "amount": 15131686190848},
            {"value": "480.215198", "amount": 4087767066542},
        ]
        prog_price = dist_price(prog, 6)
        for d in dist_entries:
            assert dist_price(d, 6) == pytest.approx(prog_price, rel=1e-3)


class TestCoreExtrasHistoricAccess:
    """Testing class for :py:func:`core.templatetags.core_extras.historic_access`."""

    def test_core_extras_historic_access_for_profile(self, mocker):
        profile = mocker.MagicMock()
        profile.can_access_historic_widget.return_value = True
        assert historic_access(profile, 3) is True
        profile.can_access_historic_widget.assert_called_once_with(3)

    def test_core_extras_historic_access_for_none(self):
        assert historic_access(None, 3) is False


class TestCoreExtrasExplorerTags:
    """Testing class for the explorer template tags."""

    def _request(self, mocker, *, authenticated, explorer="lora"):
        """Return a fake request whose viewer resolves to `explorer`."""
        profile = mocker.Mock()
        profile.preferred_explorer_or_default.return_value = explorer
        user = mocker.Mock(is_authenticated=authenticated, profile=profile)
        return mocker.Mock(user=user)

    def test_core_extras_explorer_url_defaults_to_allo_for_anonymous(self, mocker):
        context = {"request": self._request(mocker, authenticated=False)}
        assert explorer_url(context, "address", "ADDR") == (
            "https://allo.info/account/ADDR"
        )

    def test_core_extras_explorer_url_uses_viewer_preference(self, mocker):
        context = {"request": self._request(mocker, authenticated=True)}
        assert explorer_url(context, "asset", 7) == (
            "https://lora.algokit.io/mainnet/asset/7"
        )

    def test_core_extras_explorer_url_context_var_overrides(self, mocker):
        context = {"preferred_explorer": "pera"}
        assert explorer_url(context, "asset", 7) == (
            "https://explorer.perawallet.app/asset/7"
        )

    def test_core_extras_explorer_url_explicit_argument_wins(self, mocker):
        context = {"request": self._request(mocker, authenticated=True)}
        assert explorer_url(context, "asset", 7, "algosurf") == (
            "https://algo.surf/asset/7"
        )

    def test_core_extras_explorer_url_no_request_defaults_to_allo(self):
        assert explorer_url({}, "transaction", "TX") == "https://allo.info/tx/TX"

    def test_core_extras_explorer_url_signed_in_without_a_profile(self, mocker):
        """An authenticated user is not the same thing as a user with a profile.

        A profile is created by a signal, and there are two moments when the
        two come apart: partway through a social or wallet sign-up, and on the
        superuser somebody made with ``createsuperuser`` on an older database.
        Both would reach this tag as ``user.is_authenticated`` with no
        ``profile`` attribute, and reading the preference off it would raise
        inside a template tag -- which Django renders as an empty string, so
        every explorer link on the page would silently become ``https:///``.
        """
        user = mocker.Mock(is_authenticated=True)
        # `Mock` invents any attribute asked of it, so the absence has to be
        # arranged rather than assumed -- which is the whole reason this test
        # was not already here.
        del user.profile
        context = {"request": mocker.Mock(user=user)}

        assert explorer_url(context, "address", "ADDR") == (
            "https://allo.info/account/ADDR"
        )

    def test_core_extras_explorer_base_uses_viewer_preference(self, mocker):
        context = {"request": self._request(mocker, authenticated=True)}
        assert explorer_base(context) == "https://lora.algokit.io/mainnet/"

    def test_core_extras_explorer_name_uses_viewer_preference(self, mocker):
        context = {
            "request": self._request(mocker, authenticated=True, explorer="pera")
        }
        assert explorer_name(context) == "Pera Explorer"

    def test_core_extras_explorer_tx_path_uses_viewer_preference(self, mocker):
        context = {
            "request": self._request(mocker, authenticated=True, explorer="pera")
        }
        assert explorer_tx_path(context) == "tx/"

    def test_program_url_returns_standard_url_as_is(self):
        context = {}
        standard_url = "https://my-custom-app.com/about"
        assert program_url(context, standard_url) == standard_url

    def test_program_url_application_returns_explorer_link(self, mocker):
        context = {"request": self._request(mocker, authenticated=True)}
        # Assuming lora handles application URLs similarly to assets
        assert program_url(context, "application=123") == (
            "https://lora.algokit.io/mainnet/application/123"
        )

    def test_program_url_address_returns_explorer_link(self, mocker):
        context = {"request": self._request(mocker, authenticated=False)}
        # Unauthenticated defaults to allo.info, which maps "address" to "/account/"
        assert program_url(context, "address=VCMJK...") == (
            "https://allo.info/account/VCMJK..."
        )

    def test_program_url_invalid_application_id_returns_as_is(self):
        context = {}
        invalid_app = "application=ABC_NOT_NUMERIC"
        assert program_url(context, invalid_app) == invalid_app

    def test_program_url_handles_non_string_gracefully(self):
        assert program_url({}, None) is None

    def test_program_url_unsupported_entity_returns_as_is(self):
        context = {}
        # Our function only looks for 'address=' and 'application='
        unsupported = "asset=123456"
        assert program_url(context, unsupported) == unsupported

    def test_program_url_empty_string_returns_as_is(self):
        context = {}
        assert program_url(context, "") == ""

    def test_program_url_prefix_not_at_start_returns_as_is(self):
        context = {}
        # Has 'application=' inside it, but not at the start
        url_with_query = "https://example.com/api?application=123"
        assert program_url(context, url_with_query) == url_with_query

    def test_program_url_application_empty_value_returns_as_is(self):
        context = {}
        empty_app = "application="
        # "" is not numeric, so it should trigger the early return inside the loop
        assert program_url(context, empty_app) == empty_app

    def test_program_url_address_empty_value_returns_explorer_link(self, mocker):
        context = {"request": self._request(mocker, authenticated=False)}
        # Unauthenticated defaults to allo.info, which maps "address" to "/account/"
        # Since it passes the `if entity == "application"` check (it's an address),
        # it will pass an empty string to the explorer_link function.
        assert program_url(context, "address=") == "https://allo.info/account/"

    def test_program_url_address_is_numeric_returns_explorer_link(self, mocker):
        context = {"request": self._request(mocker, authenticated=True)}
        # An all-numeric address is technically valid string data for an address check
        assert program_url(context, "address=123456") == (
            "https://lora.algokit.io/mainnet/account/123456"
        )


class TestCoreExtrasFoldCounts:
    """The load-more label's arithmetic, used by both designs.

    Both filters exist because Django's ``add`` cannot subtract one variable
    from another. What is worth pinning here is that the number the label names
    is the number the control then reveals: a section whose counts disagree
    renders "Show 3 more" over a button that reveals twenty, which is how the
    magnitude rule this replaced ended up lying about itself.
    """

    def test_core_extras_beyond_counts_the_whole_tail(self):
        assert beyond(list(range(50)), 20) == 30

    def test_core_extras_beyond_of_nothing_is_zero(self):
        assert beyond([], 20) == 0

    @pytest.mark.parametrize("shown", [None, "", "twenty"])
    def test_core_extras_beyond_survives_a_missing_batch_size(self, shown):
        """A template rendered before its context arrived passes a string."""
        assert beyond(list(range(50)), shown) == 0

    def test_core_extras_beyond_is_never_negative(self):
        """"Show -3 more assets" is worse than showing no control at all."""
        assert beyond(list(range(3)), 20) == 0

    def test_core_extras_next_batch_is_capped_at_one_batch(self):
        """The label names what one press does, not what the section holds."""
        assert next_batch(list(range(50)), 20) == 20

    def test_core_extras_next_batch_is_the_remainder_when_that_is_smaller(self):
        """The last press reveals what is left, and says so."""
        assert next_batch(list(range(28)), 20) == 8

    def test_core_extras_next_batch_of_a_short_section_is_zero(self):
        """Nothing folded, so no control renders and nothing is promised."""
        assert next_batch(list(range(12)), 20) == 0

    def test_core_extras_next_batch_of_nothing_is_zero(self):
        assert next_batch([], 20) == 0

    @pytest.mark.parametrize("shown", [None, "", "twenty"])
    def test_core_extras_next_batch_survives_a_missing_batch_size(self, shown):
        assert next_batch(list(range(50)), shown) == 0

    def test_core_extras_next_batch_never_exceeds_the_tail(self):
        """Whatever the batch size, the promise cannot outrun the rows."""
        for total in range(0, 45):
            rows = list(range(total))
            assert next_batch(rows, 20) <= beyond(rows, 20)
