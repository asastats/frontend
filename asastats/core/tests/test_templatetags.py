"""Testing module for core app's template tags and filters."""

import pytest

from core.templatetags.core_extras import (
    abs_value,
    amount_repr,
    asa_icon,
    bundle_hash,
    dict_get,
    dist_height,
    get_styling,
    has_styling,
    historic_access,
    historic_data,
    integer_comma,
    invert_price,
    is_distribution,
    is_negative,
    list_item,
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
    # The asa_icon signature changed in Phase 2: it now takes a single
    # serialized asaitem dict (with .asset and .programs) rather than the
    # legacy (asset_id, apps) positional pair. The Lofty/ANote override is
    # determined by scanning three independent signals (provider name on
    # any program, asset.name, and linked URLs) so the filter works whether
    # or not the serialized payload exposes a provider on the program.
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
        assert asa_icon(item) == "icons/providers/lofty.png"

    def test_filters_asa_icon_returns_lofty_icon_for_lofty_asset_name(self):
        # Real Lofty assets in production carry the prefix on asset.name
        # and have no provider on their Balance program; the filter must
        # still recognise them.
        item = self._asaitem(asset_id=505, name="Lofty 3878 Windermere Rd")
        assert asa_icon(item) == "icons/providers/lofty.png"

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
        assert asa_icon(item) == "icons/providers/lofty.png"

    def test_filters_asa_icon_returns_usdc_icon_for_lofty_signals_and_usdc(self):
        # USDC is hard-excluded from the override; it's the quote currency
        # and never carries meaningful provider semantics.
        item = self._asaitem(
            asset_id=31566704,
            unit="USDC",
            programs=[{"program": {"provider": {"name": "Lofty"}}}],
        )
        assert asa_icon(item) == "icons/31566704t.png"

    def test_filters_asa_icon_returns_anote_icon_for_anote_provider(self):
        item = self._asaitem(
            asset_id=505,
            programs=[{"program": {"provider": {"name": "ANote"}}}],
        )
        assert asa_icon(item) == "icons/providers/anote.png"

    def test_filters_asa_icon_returns_anote_icon_for_anmc_unit_prefix(self):
        # ANote music tokens use the anmc unit prefix; their asset names
        # vary per release so the unit prefix is the reliable signal.
        item = self._asaitem(asset_id=505, unit="anmc1")
        assert asa_icon(item) == "icons/providers/anote.png"

    def test_filters_asa_icon_returns_image_path(self):
        # No override signals — fall back to the standard thumbnail path.
        item = self._asaitem(asset_id=226701642, name="Yieldly", unit="YLDY")
        assert asa_icon(item) == "icons/226701642t.png"

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
    @pytest.mark.parametrize(
        "index,result",
        [
            (0, "26,872.283825"),
            (1, "355,029"),
            (2, "10,000.00100"),
            (3, "3.0000000010"),
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
    # used under static/icons/providers/: lowercase, whitespace stripped,
    # no dashes. Matches the existing static-file naming (livecoinwatch.png,
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
        assert provider_icon(name) == result

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
        # 10092956 / 1e6 = 10.092956
        assert "10.092956" in result


class TestCoreExtrasHistoricAccess:
    """Testing class for :py:func:`core.templatetags.core_extras.historic_access`."""

    def test_core_extras_historic_access_for_profile(self, mocker):
        profile = mocker.MagicMock()
        profile.can_access_historic_widget.return_value = True
        assert historic_access(profile, 3) is True
        profile.can_access_historic_widget.assert_called_once_with(3)

    def test_core_extras_historic_access_for_none(self):
        assert historic_access(None, 3) is False
