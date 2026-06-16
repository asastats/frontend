"""Testing module for :py:mod:`api.helpers` module."""

import types

import pytest
from rest_framework.serializers import ValidationError

import api.serializers
from api.data import (
    API_EXAMPLE_ADDRESS1,
    API_EXAMPLE_ADDRESS2,
    API_EXAMPLE_BUNDLE1,
)
from api.helpers import (
    _check_program_name,
    _check_program_type,
    _check_provider_name,
    _convert_algo_value_to_usd,
    _convert_programs_values_to_usd,
    _extract_account_markets,
    _extract_account_programs,
    _extract_account_providers,
    _filter_nfts_by_market,
    _filter_nfts_by_sale_type,
    _filter_programs_by_program,
    _filter_programs_by_provider,
    _filter_programs_by_type,
    _remove_duplicated_dicts_and_sort_by_name,
    convert_account_values_to_usd,
    convert_asaitems_values_to_usd,
    convert_items_values_to_usd,
    convert_nftcollections_values_to_usd,
    extract_account_entities,
    extract_account_headers,
    extract_asaitem,
    extract_asaitems_headers,
    extract_asaitems_program,
    extract_asaitems_program_type,
    extract_asaitems_provider,
    extract_nftcollection,
    extract_nftcollections_headers,
    extract_nftcollections_market,
    extract_nftcollections_sale_type,
    extract_nftitem,
    extract_nftitems_from_nftcollections,
    extract_nftitems_headers,
    extract_nftitems_market,
    extract_nftitems_sale_type,
    extract_top_account_items,
    get_lib_doc_excludes,
    preprocessing_filter_spec,
    validate_address,
    validate_bundle,
    validate_nfd_name,
    validate_raw_addresses,
)
from utils.constants.apiv2 import (
    INVALID_ADDRESS_INPUT_TEXT,
    INVALID_INPUT_TEXT,
    INVALID_NFD_NAME_TEXT,
    INVALID_RAW_TEXT,
)
from utils.constants.core import INVALID_ADDRESS_TEXT, INVALID_BUNDLE_TEXT


class TestApiHelpersUsdConversion:
    """Testing class for :py:mod:`api.helpers` USD conversion functions."""

    # # _convert_algo_value_to_usd
    def test_api_helpers_convert_algo_value_to_usd_functionality(self):
        assert _convert_algo_value_to_usd("2", "1.5") == "3.000000"

    # # convert_asaitems_values_to_usd
    def test_api_helpers_convert_asaitems_values_to_usd_functionality(self, mocker):
        mocker.patch("api.helpers._convert_algo_value_to_usd", return_value="9")
        mocked_programs = mocker.patch(
            "api.helpers._convert_programs_values_to_usd", return_value=["P"]
        )
        asaitems = [{"asset": {"id": 1}, "value": "2", "programs": ["x"]}]
        returned = convert_asaitems_values_to_usd(asaitems, "1.5")
        assert returned == [{"asset": {"id": 1}, "value": "9", "programs": ["P"]}]
        mocked_programs.assert_called_once_with(["x"], "1.5")

    # # convert_items_values_to_usd
    def test_api_helpers_convert_items_values_to_usd_functionality(self, mocker):
        mocker.patch("api.helpers._convert_algo_value_to_usd", return_value="9")
        items = [{"name": "a", "value": "2", "price": "3"}]
        returned = convert_items_values_to_usd(
            items, "1.5", process_keys=["value", "price"]
        )
        assert returned == [{"name": "a", "value": "9", "price": "9"}]

    # # convert_nftcollections_values_to_usd
    def test_api_helpers_convert_nftcollections_values_to_usd_functionality(
        self, mocker
    ):
        mocker.patch("api.helpers._convert_algo_value_to_usd", return_value="9")
        mocked_items = mocker.patch(
            "api.helpers.convert_items_values_to_usd", return_value=["N"]
        )
        nftcollections = [{"name": "c", "value": "2", "nfts": ["n"]}]
        returned = list(convert_nftcollections_values_to_usd(nftcollections, "1.5"))
        assert returned == [{"name": "c", "value": "9", "nfts": ["N"]}]
        mocked_items.assert_called_once_with(
            ["n"], "1.5", process_keys=["value", "price"]
        )

    # # _convert_programs_values_to_usd
    def test_api_helpers_convert_programs_values_to_usd_with_linked(self, mocker):
        mocker.patch("api.helpers._convert_algo_value_to_usd", return_value="9")
        mocked_items = mocker.patch(
            "api.helpers.convert_items_values_to_usd", return_value=["L"]
        )
        programs = [{"name": "p", "value": "2", "linked": ["x"]}]
        returned = _convert_programs_values_to_usd(programs, "1.5")
        assert returned == [{"name": "p", "value": "9", "linked": ["L"]}]
        mocked_items.assert_called_once_with(["x"], "1.5")

    def test_api_helpers_convert_programs_values_to_usd_without_linked(self, mocker):
        mocker.patch("api.helpers._convert_algo_value_to_usd", return_value="9")
        mocked_items = mocker.patch("api.helpers.convert_items_values_to_usd")
        programs = [{"name": "p", "value": "2"}]
        returned = _convert_programs_values_to_usd(programs, "1.5")
        assert returned == [{"name": "p", "value": "9"}]
        mocked_items.assert_not_called()

    # # convert_account_values_to_usd
    def test_api_helpers_convert_account_values_to_usd_functionality(self, mocker):
        mocked_asaitems = mocker.patch(
            "api.helpers.convert_asaitems_values_to_usd", return_value="ASAS"
        )
        mocked_nfts = mocker.patch(
            "api.helpers.convert_nftcollections_values_to_usd", return_value="NFTS"
        )
        serialized_data = {
            "account_info": {"addresses": ["A"]},
            "asaitems": ["i"],
            "nftcollections": ["c"],
            "total": {"x": 1},
        }
        returned = convert_account_values_to_usd(serialized_data, "1.5")
        assert returned["account_info"] == {"addresses": ["A"], "values_in": "USD"}
        assert returned["asaitems"] == "ASAS"
        assert returned["nftcollections"] == "NFTS"
        assert returned["total"] == {"x": 1}
        mocked_asaitems.assert_called_once_with(["i"], "1.5")
        mocked_nfts.assert_called_once_with(["c"], "1.5")


class TestApiHelpersExtractHelpers:
    """Testing class for :py:mod:`api.helpers` extract helpers functions."""

    # # _check_provider_name
    @pytest.mark.parametrize(
        "provider,name",
        [
            ("provider", "Provider"),
            ("some-provider", "Some provider"),
            ("another-one", "Another One"),
            ("yet-another-one", "yet another one"),
            ("first", "First name"),
            ("exa", "EXA market"),
            ("EXA", "EXA Market"),
            ("EXA-Market", "EXA Market"),
            ("cometa", "Cometa"),
            ("Pact", "Pact"),
        ],
    )
    def test_api_helpers_check_provider_name_returns_true(self, provider, name):
        assert _check_provider_name(provider, name) is True

    @pytest.mark.parametrize(
        "provider,name",
        [
            ("provider", "Providere"),
            ("some-provider", "Some"),
            ("another-one", "Another"),
            ("yet-another-one", "yet another"),
            ("first", "Name First"),
            ("market", "EXA market"),
            ("Market", "EXA Market"),
            ("market-exa", "EXA Market"),
            ("cometa1", "Cometa"),
            ("cometa-", "Cometa"),
        ],
    )
    def test_api_helpers_check_provider_name_returns_false(self, provider, name):
        assert _check_provider_name(provider, name) is False


class TestApiHelpersCheckProgramTypeBranches:
    """Testing class for :py:func:`api.helpers._check_program_type` branches."""

    # # _check_program_name
    @pytest.mark.parametrize(
        "program,name",
        [
            ("program", "Program"),
            ("some-program", "Some program"),
            ("another-one", "Another One"),
            ("yet-another-one", "yet another one"),
            ("cometa-stake", "Cometa stake"),
            ("cometa-staking", "Cometa stake"),
            ("pact-farm", "Pact farm"),
            ("pact-farming", "Pact farm"),
            ("Pact-farm", "Pact farm"),
            ("Balance", "Balance"),
            ("balance", "Balance"),
            ("folks-governance-9", "Folks governance #{0}"),
            ("algorand-governance", "Algorand governance"),
            ("Algorand-governance", "Algorand governance"),
            ("lofty-something-orders", "Lofty foobar orders"),
            ("defly-limit", "Defly limit orders"),
            ("defly-limit-orders", "Defly limit orders"),
            ("exa-swap-fee", "EXA Swap fee"),
            ("exa-offer-fee", "EXA Offer fee"),
            ("exa-escrows-fee", "EXA escrows fee"),
            ("compx-escrows-fee", "CompX escrows fee"),
        ],
    )
    def test_api_helpers_check_program_name_returns_true(self, program, name):
        assert _check_program_name(program, name) is True

    @pytest.mark.parametrize(
        "program,name",
        [
            ("provider", "Providere"),
            ("some-provider", "Some"),
            ("another-one", "Another"),
            ("yet-another-one", "yet another"),
            ("first", "Name First"),
            ("market", "EXA market"),
            ("Market", "EXA Market"),
            ("market-exa", "EXA Market"),
            ("cometa1", "Cometa"),
        ],
    )
    def test_api_helpers_check_program_name_returns_false(self, program, name):
        assert _check_program_name(program, name) is False

    # # _check_program_type
    @pytest.mark.parametrize(
        "type_slug,check_name,check_type",
        [
            ("program", "Program", ""),
            ("stake", "Cometa stake", ""),
            ("staking", "Cometa stake", ""),
            ("farm", "Pact farm", ""),
            ("farming", "Pact farm", ""),
            ("Farm", "Pact farm", ""),
            ("Balance", "Balance", ""),
            ("balance", "Balance", ""),
            ("governance", "Folks governance #{0}", ""),
            ("governance", "Algorand governance", ""),
            ("governance", "Algorand governance", ""),
            ("orders", "Lofty foobar orders", ""),
            ("orders", "Defly limit orders", ""),
            ("fee", "EXA Swap fee", ""),
            ("fee", "EXA Offer fee", ""),
            ("fee", "EXA escrows fee", ""),
            ("fee", "CompX escrows fee", ""),
        ],
    )
    def test_api_helpers_check_program_type_returns_true(
        self, type_slug, check_name, check_type
    ):
        assert _check_program_type(type_slug, check_name, check_type) is True

    def test_api_helpers_check_program_type_strips_numeric_suffix(self):
        assert _check_program_type("governance-2", "Governance", "governance") is True

    def test_api_helpers_check_program_type_returns_false(self):
        assert _check_program_type("foo", "bar", "baz") is False


class TestApiHelpersExtractAsa:
    """Testing class for :py:mod:`api.helpers` ASA based extract functions."""

    # # _filter_programs_by_program
    def test_api_helpers_filter_programs_by_program_for_no_programs(self, mocker):
        program_slug = "program"
        programs = []
        mocked_check = mocker.patch("api.helpers._check_provider_name")
        returned = _filter_programs_by_program(program_slug, programs)
        assert returned == []
        mocked_check.assert_not_called()

    def test_api_helpers_filter_programs_by_program_functionality(self, mocker):
        mocked_check = mocker.patch(
            "api.helpers._check_program_name",
            side_effect=[True, False, True, False],
        )
        program_slug = "program"
        programs = [
            {"program": {"name": "foo1"}, "provider": {"name": "something1"}},
            {"program": {"name": "foo2"}, "provider": {"name": "something2"}},
            {"program": {"bar": "foo3"}, "provider": {"name": "something3"}},
            {"program": {"name": "foo4"}, "provider": {"name": "something4"}},
            {"program": {"name": "foo5"}, "provider": {"name": "something5"}},
        ]
        returned = _filter_programs_by_program(program_slug, programs)
        assert returned == [
            {"program": {"name": "foo1"}, "provider": {"name": "something1"}},
            {"program": {"name": "foo4"}, "provider": {"name": "something4"}},
        ]
        calls = [
            mocker.call(program_slug, "foo1"),
            mocker.call(program_slug, "foo2"),
            mocker.call(program_slug, "foo4"),
            mocker.call(program_slug, "foo5"),
        ]
        mocked_check.assert_has_calls(calls, any_order=True)
        assert mocked_check.call_count == 4

    # # _filter_programs_by_provider
    def test_api_helpers_filter_programs_by_provider_for_no_programs(self, mocker):
        provider = "provider"
        programs = []
        mocked_check = mocker.patch("api.helpers._check_provider_name")
        returned = _filter_programs_by_provider(provider, programs)
        assert returned == []
        mocked_check.assert_not_called()

    def test_api_helpers_filter_programs_by_provider_functionality(self, mocker):
        mocked_check = mocker.patch(
            "api.helpers._check_provider_name",
            side_effect=[True, False, True, False],
        )
        provider = "provider"
        programs = [
            {"program": {"name": "foo1", "provider": {"name": "something1"}}},
            {"program": {"name": "foo2", "provider": {"name": "something2"}}},
            {"program": {"name": "foo3", "provider": {"foo": "something3"}}},
            {"program": {"name": "foo4", "provider": {"name": "something4"}}},
            {"program": {"name": "foo5", "provider": {"name": "something5"}}},
        ]
        returned = _filter_programs_by_provider(provider, programs)
        assert returned == [
            {"program": {"name": "foo1", "provider": {"name": "something1"}}},
            {"program": {"name": "foo4", "provider": {"name": "something4"}}},
        ]
        calls = [
            mocker.call(provider, "something1"),
            mocker.call(provider, "something2"),
            mocker.call(provider, "something4"),
            mocker.call(provider, "something5"),
        ]
        mocked_check.assert_has_calls(calls, any_order=True)
        assert mocked_check.call_count == 4

    # # _filter_programs_by_type
    def test_api_helpers_filter_programs_by_type_for_no_programs(self, mocker):
        program_type = "program_type"
        programs = []
        mocked_check = mocker.patch("api.helpers._check_program_type")
        returned = _filter_programs_by_type(program_type, programs)
        assert returned == []
        mocked_check.assert_not_called()

    def test_api_helpers_filter_programs_by_type_functionality(self, mocker):
        mocked_check = mocker.patch(
            "api.helpers._check_program_type",
            side_effect=[True, False, True, True],
        )
        program_type = "program_type"
        programs = [
            {
                "program": {"name": "foo1", "type": "bar1"},
                "provider": {"name": "something1"},
            },
            {"program": {"name": "foo2"}, "provider": {"name": "something2"}},
            {"program": {"bar": "foo3"}, "provider": {"name": "something3"}},
            {"program": {"type": "bar4"}, "provider": {"name": "something4"}},
            {"program": {"name": "foo5"}, "provider": {"name": "something5"}},
        ]
        returned = _filter_programs_by_type(program_type, programs)
        assert returned == [
            {
                "program": {"name": "foo1", "type": "bar1"},
                "provider": {"name": "something1"},
            },
            {"program": {"type": "bar4"}, "provider": {"name": "something4"}},
            {"program": {"name": "foo5"}, "provider": {"name": "something5"}},
        ]
        calls = [
            mocker.call(program_type, "foo1", "bar1"),
            mocker.call(program_type, "foo2", ""),
            mocker.call(program_type, "", "bar4"),
            mocker.call(program_type, "foo5", ""),
        ]
        mocked_check.assert_has_calls(calls, any_order=True)
        assert mocked_check.call_count == 4

    # # extract_asaitem
    def test_api_helpers_extract_asaitem_for_no_asaitems(self):
        asset_id = 505
        asaitems = []
        returned = extract_asaitem(asset_id, asaitems)
        assert returned == {}

    def test_api_helpers_extract_asaitem_for_no_asset_id(self):
        asset_id = 505
        asaitems = [{"asset": {"id": 100}}, {"asset": {"id": 200}}]
        returned = extract_asaitem(asset_id, asaitems)
        assert returned == {}

    def test_api_helpers_extract_asaitem_functionality(self):
        asset_id = 505
        asaitems = [{"asset": {"id": 100}}, {"asset": {"id": asset_id}}]
        returned = extract_asaitem(asset_id, asaitems)
        assert returned == {"asset": {"id": asset_id}}

    # # extract_asaitems_headers
    def test_api_helpers_extract_asaitems_headers_for_no_asaitems(self):
        asaitems = []
        returned = extract_asaitems_headers(asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_asaitems_headers_functionality(self):
        asaitems = [
            {
                "value": 100,
                "amount": 10,
                "programs": ["program1"],
                "asset": {"id": 100, "links": []},
            },
            {
                "value": 200,
                "amount": 20,
                "programs": ["program2", "program3"],
                "asset": {"id": 200, "links": ["link3", "link4"]},
            },
            {"value": 300, "programs": [], "asset": {"id": 300, "links": ["link5"]}},
        ]
        returned = extract_asaitems_headers(asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == [
            {
                "value": 100,
                "amount": 10,
                "programs": [],
                "asset": {"id": 100, "links": []},
            },
            {
                "value": 200,
                "amount": 20,
                "programs": [],
                "asset": {"id": 200, "links": []},
            },
            {"value": 300, "programs": [], "asset": {"id": 300, "links": []}},
        ]

    # # extract_asaitems_program
    def test_api_helpers_extract_asaitems_program_for_no_program(self):
        program = ""
        asaitems = [
            {
                "value": 100,
                "amount": 10,
                "asset": {"id": 100, "links": []},
                "programs": [
                    {"program": {"name": "foo1"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
            }
        ]
        returned = extract_asaitems_program(program, asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_asaitems_program_for_no_asaitems(self):
        program = "program"
        asaitems = []
        returned = extract_asaitems_program(program, asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_asaitems_program_functionality(self, mocker):
        mocked_filter = mocker.patch(
            "api.helpers._filter_programs_by_program",
            side_effect=[
                [
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
                [
                    {"program": {"name": "foo5"}, "provider": {"name": "something"}},
                ],
                [],
            ],
        )
        program = "program"
        asaitems = [
            {
                "value": 100,
                "amount": 10,
                "asset": {"id": 100, "links": []},
                "programs": [
                    {"program": {"name": "foo1"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
            },
            {
                "value": 200,
                "amount": 20,
                "asset": {"id": 200, "links": ["link3", "link4"]},
                "programs": [
                    {"program": {"name": "foo3"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo4"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo5"}, "provider": {"name": "something"}},
                ],
            },
            {"value": 300, "asset": {"id": 300, "links": ["link5"]}, "programs": []},
        ]
        returned = extract_asaitems_program(program, asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == [
            {
                "asset": {"id": 100, "links": []},
                "programs": [
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
            },
            {
                "asset": {"id": 200, "links": ["link3", "link4"]},
                "programs": [
                    {"program": {"name": "foo5"}, "provider": {"name": "something"}},
                ],
            },
        ]
        calls = [
            mocker.call(program, asaitems[0].get("programs")),
            mocker.call(program, asaitems[1].get("programs")),
            mocker.call(program, asaitems[2].get("programs")),
        ]
        mocked_filter.assert_has_calls(calls, any_order=True)
        assert mocked_filter.call_count == 3

    # # extract_asaitems_provider
    def test_api_helpers_extract_asaitems_provider_for_no_provider(self):
        provider = ""
        asaitems = [
            {
                "value": 100,
                "amount": 10,
                "asset": {"id": 100, "links": []},
                "programs": [
                    {"program": {"name": "foo1"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
            }
        ]
        returned = extract_asaitems_provider(provider, asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_asaitems_provider_for_no_asaitems(self):
        provider = "provider"
        asaitems = []
        returned = extract_asaitems_provider(provider, asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_asaitems_provider_functionality(self, mocker):
        mocked_filter = mocker.patch(
            "api.helpers._filter_programs_by_provider",
            side_effect=[
                [
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
                [
                    {"program": {"name": "foo5"}, "provider": {"name": "something"}},
                ],
                [],
            ],
        )
        provider = "provider"
        asaitems = [
            {
                "value": 100,
                "amount": 10,
                "asset": {"id": 100, "links": []},
                "programs": [
                    {"program": {"name": "foo1"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
            },
            {
                "value": 200,
                "amount": 20,
                "asset": {"id": 200, "links": ["link3", "link4"]},
                "programs": [
                    {"program": {"name": "foo3"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo4"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo5"}, "provider": {"name": "something"}},
                ],
            },
            {"value": 300, "asset": {"id": 300, "links": ["link5"]}, "programs": []},
        ]
        returned = extract_asaitems_provider(provider, asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == [
            {
                "asset": {"id": 100, "links": []},
                "programs": [
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
            },
            {
                "asset": {"id": 200, "links": ["link3", "link4"]},
                "programs": [
                    {"program": {"name": "foo5"}, "provider": {"name": "something"}},
                ],
            },
        ]
        calls = [
            mocker.call(provider, asaitems[0].get("programs")),
            mocker.call(provider, asaitems[1].get("programs")),
            mocker.call(provider, asaitems[2].get("programs")),
        ]
        mocked_filter.assert_has_calls(calls, any_order=True)
        assert mocked_filter.call_count == 3

    # # extract_asaitems_program_type
    def test_api_helpers_extract_asaitems_program_type_for_no_program_type(self):
        program_type = ""
        asaitems = [
            {
                "value": 100,
                "amount": 10,
                "asset": {"id": 100, "links": []},
                "programs": [
                    {"program": {"name": "foo1"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
            }
        ]
        returned = extract_asaitems_program_type(program_type, asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_asaitems_program_type_for_no_asaitems(self):
        program_type = "program_type"
        asaitems = []
        returned = extract_asaitems_program_type(program_type, asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_asaitems_program_type_functionality(self, mocker):
        mocked_filter = mocker.patch(
            "api.helpers._filter_programs_by_type",
            side_effect=[
                [
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
                [
                    {"program": {"name": "foo5"}, "provider": {"name": "something"}},
                ],
                [],
            ],
        )
        program_type = "program_type"
        asaitems = [
            {
                "value": 100,
                "amount": 10,
                "asset": {"id": 100, "links": []},
                "programs": [
                    {"program": {"name": "foo1"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
            },
            {
                "value": 200,
                "amount": 20,
                "asset": {"id": 200, "links": ["link3", "link4"]},
                "programs": [
                    {"program": {"name": "foo3"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo4"}, "provider": {"name": "something"}},
                    {"program": {"name": "foo5"}, "provider": {"name": "something"}},
                ],
            },
            {"value": 300, "asset": {"id": 300, "links": ["link5"]}, "programs": []},
        ]
        returned = extract_asaitems_program_type(program_type, asaitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == [
            {
                "asset": {"id": 100, "links": []},
                "programs": [
                    {"program": {"name": "foo2"}, "provider": {"name": "something"}},
                ],
            },
            {
                "asset": {"id": 200, "links": ["link3", "link4"]},
                "programs": [
                    {"program": {"name": "foo5"}, "provider": {"name": "something"}},
                ],
            },
        ]
        calls = [
            mocker.call(program_type, asaitems[0].get("programs")),
            mocker.call(program_type, asaitems[1].get("programs")),
            mocker.call(program_type, asaitems[2].get("programs")),
        ]
        mocked_filter.assert_has_calls(calls, any_order=True)
        assert mocked_filter.call_count == 3


class TestApiHelpersExtractNft:
    """Testing class for :py:mod:`api.helpers` NFT related extract functions."""

    # # _filter_nfts_by_market
    def test_api_helpers_filter_nfts_by_market_for_no_nfts(self, mocker):
        market = "market"
        nfts = []
        mocked_check = mocker.patch("api.helpers._check_provider_name")
        returned = _filter_nfts_by_market(market, nfts)
        assert returned == []
        mocked_check.assert_not_called()

    def test_api_helpers_filter_nfts_by_market_functionality(self, mocker):
        mocked_check = mocker.patch(
            "api.helpers._check_provider_name",
            side_effect=[False, False, True, False, False, True, False, True],
        )
        market = "market"
        nfts = [
            {
                "value": "1.0",
                "nft": {
                    "name": "foo1",
                    "last_purchase": {"market": {"name": "something1"}},
                    "max_purchase": {"market": {"name": "something2"}},
                    "listings": [{"market": {"name": "something3"}}],
                    "floor": [{"market": {"name": "something4"}}],
                },
            },
            {
                "value": "2.0",
                "nft": {
                    "name": "foo2",
                    "max_purchase": {"market": {"name": "something5"}},
                    "listings": None,
                },
            },
            {
                "value": "3.0",
                "nft": {
                    "name": "foo3",
                    "last_purchase": None,
                    "listings": [
                        {"market": {"name": "something6"}},
                        {"market": {"name": "something7"}},
                    ],
                    "floor": None,
                },
            },
            {
                "value": "4.0",
                "nft": {
                    "name": "foo4",
                    "last_purchase": {"market": {"name": "something8"}},
                    "max_purchase": None,
                    "listings": None,
                },
            },
            {
                "value": "5.0",
                "nft": {
                    "name": "foo5",
                    "max_purchase": {"market": {"name": "something9"}},
                    "floor": [{"market": {"name": "something10"}}],
                },
            },
        ]
        returned = _filter_nfts_by_market(market, nfts)
        assert returned == [
            {
                "value": "1.0",
                "nft": {
                    "name": "foo1",
                    "last_purchase": {"market": {"name": "something1"}},
                    "max_purchase": {"market": {"name": "something2"}},
                    "listings": [{"market": {"name": "something3"}}],
                    "floor": [{"market": {"name": "something4"}}],
                },
            },
            {
                "value": "3.0",
                "nft": {
                    "name": "foo3",
                    "last_purchase": None,
                    "listings": [
                        {"market": {"name": "something6"}},
                        {"market": {"name": "something7"}},
                    ],
                    "floor": None,
                },
            },
            {
                "value": "5.0",
                "nft": {
                    "name": "foo5",
                    "max_purchase": {"market": {"name": "something9"}},
                    "floor": [{"market": {"name": "something10"}}],
                },
            },
        ]
        calls = [
            mocker.call(market, "something1"),
            mocker.call(market, "something2"),
            mocker.call(market, "something3"),
            mocker.call(market, "something5"),
            mocker.call(market, "something6"),
            mocker.call(market, "something7"),
            mocker.call(market, "something8"),
            mocker.call(market, "something9"),
        ]
        mocked_check.assert_has_calls(calls, any_order=True)
        assert mocked_check.call_count == 8

    # # _filter_nfts_by_sale_type
    def test_api_helpers_filter_nfts_by_sale_type_for_no_nfts(self, mocker):
        sale_type = "purchase"
        nfts = []
        mocked_check = mocker.patch("api.helpers._check_provider_name")
        returned = _filter_nfts_by_sale_type(sale_type, nfts)
        assert returned == []
        mocked_check.assert_not_called()

    def test_api_helpers_filter_nfts_by_sale_type_for_purchase(self):
        sale_type = "purchase"
        nfts = [
            {
                "value": "1.0",
                "nft": {
                    "name": "foo1",
                    "listings": [{"market": {"name": "something3"}}],
                    "floor": [{"market": {"name": "something4"}}],
                },
            },
            {
                "value": "2.0",
                "nft": {
                    "name": "foo2",
                    "max_purchase": {"market": {"name": "something5"}},
                    "listings": None,
                },
            },
            {
                "value": "3.0",
                "nft": {
                    "name": "foo3",
                    "last_purchase": None,
                    "listings": [
                        {"market": {"name": "something6"}},
                        {"market": {"name": "something7"}},
                    ],
                    "floor": None,
                },
            },
            {
                "value": "4.0",
                "nft": {
                    "name": "foo4",
                    "max_purchase": None,
                    "listings": None,
                },
            },
            {
                "value": "5.0",
                "nft": {
                    "name": "foo5",
                    "max_purchase": {"market": {"name": "something9"}},
                    "floor": [{"market": {"name": "something10"}}],
                },
            },
        ]
        returned = _filter_nfts_by_sale_type(sale_type, nfts)
        assert returned == [nfts[1], nfts[4]]

    def test_api_helpers_filter_nfts_by_sale_type_for_no_purchase(self):
        sale_type = "no-purchase"
        nfts = [
            {
                "value": "1.0",
                "nft": {
                    "name": "foo1",
                    "listings": [{"market": {"name": "something3"}}],
                    "floor": [{"market": {"name": "something4"}}],
                },
            },
            {
                "value": "2.0",
                "nft": {
                    "name": "foo2",
                    "max_purchase": {"market": {"name": "something5"}},
                    "listings": None,
                },
            },
            {
                "value": "3.0",
                "nft": {
                    "name": "foo3",
                    "last_purchase": None,
                    "listings": [
                        {"market": {"name": "something6"}},
                        {"market": {"name": "something7"}},
                    ],
                    "floor": None,
                },
            },
            {
                "value": "4.0",
                "nft": {
                    "name": "foo4",
                    "max_purchase": None,
                    "listings": None,
                },
            },
            {
                "value": "5.0",
                "nft": {
                    "name": "foo5",
                    "max_purchase": {"market": {"name": "something9"}},
                    "floor": [{"market": {"name": "something10"}}],
                },
            },
        ]
        returned = _filter_nfts_by_sale_type(sale_type, nfts)
        assert returned == [nfts[0], nfts[2], nfts[3]]

    def test_api_helpers_filter_nfts_by_sale_type_for_listing(self):
        sale_type = "listing"
        nfts = [
            {
                "value": "1.0",
                "nft": {
                    "name": "foo1",
                    "listings": [{"market": {"name": "something3"}}],
                    "floor": [{"market": {"name": "something4"}}],
                },
            },
            {
                "value": "2.0",
                "nft": {
                    "name": "foo2",
                    "max_purchase": {"market": {"name": "something5"}},
                    "listings": None,
                },
            },
            {
                "value": "3.0",
                "nft": {
                    "name": "foo3",
                    "last_purchase": None,
                    "listings": [
                        {"market": {"name": "something6"}},
                        {"market": {"name": "something7"}},
                    ],
                    "floor": None,
                },
            },
            {
                "value": "4.0",
                "nft": {
                    "name": "foo4",
                    "max_purchase": None,
                    "listings": None,
                },
            },
            {
                "value": "5.0",
                "nft": {
                    "name": "foo5",
                    "max_purchase": {"market": {"name": "something9"}},
                    "floor": [{"market": {"name": "something10"}}],
                },
            },
        ]
        returned = _filter_nfts_by_sale_type(sale_type, nfts)
        assert returned == [nfts[0], nfts[2]]

    def test_api_helpers_filter_nfts_by_sale_type_for_no_listing(self):
        sale_type = "no-listing"
        nfts = [
            {
                "value": "1.0",
                "nft": {
                    "name": "foo1",
                    "listings": [{"market": {"name": "something3"}}],
                    "floor": [{"market": {"name": "something4"}}],
                },
            },
            {
                "value": "2.0",
                "nft": {
                    "name": "foo2",
                    "max_purchase": {"market": {"name": "something5"}},
                    "listings": None,
                },
            },
            {
                "value": "3.0",
                "nft": {
                    "name": "foo3",
                    "last_purchase": None,
                    "listings": [
                        {"market": {"name": "something6"}},
                        {"market": {"name": "something7"}},
                    ],
                    "floor": None,
                },
            },
            {
                "value": "4.0",
                "nft": {
                    "name": "foo4",
                    "max_purchase": None,
                    "listings": None,
                },
            },
            {
                "value": "5.0",
                "nft": {
                    "name": "foo5",
                    "max_purchase": {"market": {"name": "something9"}},
                    "floor": [{"market": {"name": "something10"}}],
                },
            },
        ]
        returned = _filter_nfts_by_sale_type(sale_type, nfts)
        assert returned == [nfts[1], nfts[3], nfts[4]]

    def test_api_helpers_filter_nfts_by_sale_type_for_floor(self):
        sale_type = "floor"
        nfts = [
            {
                "value": "1.0",
                "nft": {
                    "name": "foo1",
                    "listings": [{"market": {"name": "something3"}}],
                    "floor": [{"market": {"name": "something4"}}],
                },
            },
            {
                "value": "2.0",
                "nft": {
                    "name": "foo2",
                    "max_purchase": {"market": {"name": "something5"}},
                    "listings": None,
                },
            },
            {
                "value": "3.0",
                "nft": {
                    "name": "foo3",
                    "last_purchase": None,
                    "listings": [
                        {"market": {"name": "something6"}},
                        {"market": {"name": "something7"}},
                    ],
                    "floor": None,
                },
            },
            {
                "value": "4.0",
                "nft": {
                    "name": "foo4",
                    "max_purchase": None,
                    "listings": None,
                },
            },
            {
                "value": "5.0",
                "nft": {
                    "name": "foo5",
                    "max_purchase": {"market": {"name": "something9"}},
                    "floor": [{"market": {"name": "something10"}}],
                },
            },
        ]
        returned = _filter_nfts_by_sale_type(sale_type, nfts)
        assert returned == [nfts[0], nfts[4]]

    def test_api_helpers_filter_nfts_by_sale_type_for_no_floor(self):
        sale_type = "no-floor"
        nfts = [
            {
                "value": "1.0",
                "nft": {
                    "name": "foo1",
                    "listings": [{"market": {"name": "something3"}}],
                    "floor": [{"market": {"name": "something4"}}],
                },
            },
            {
                "value": "2.0",
                "nft": {
                    "name": "foo2",
                    "max_purchase": {"market": {"name": "something5"}},
                    "listings": None,
                },
            },
            {
                "value": "3.0",
                "nft": {
                    "name": "foo3",
                    "last_purchase": None,
                    "listings": [
                        {"market": {"name": "something6"}},
                        {"market": {"name": "something7"}},
                    ],
                    "floor": None,
                },
            },
            {
                "value": "4.0",
                "nft": {
                    "name": "foo4",
                    "max_purchase": None,
                    "listings": None,
                },
            },
            {
                "value": "5.0",
                "nft": {
                    "name": "foo5",
                    "max_purchase": {"market": {"name": "something9"}},
                    "floor": [{"market": {"name": "something10"}}],
                },
            },
        ]
        returned = _filter_nfts_by_sale_type(sale_type, nfts)
        assert returned == [nfts[1], nfts[2], nfts[3]]

    # # extract_nftcollections_headers
    def test_api_helpers_extract_nftcollections_headers_for_no_nftcollections(self):
        nftcollections = []
        returned = extract_nftcollections_headers(nftcollections)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_nftcollections_headers_functionality(self):
        nftcollections = [
            {
                "value": "100",
                "amount": 10,
                "nfts": [
                    {
                        "value": "1.0",
                        "nft": {
                            "name": "foo1",
                            "last_purchase": {"market": {"name": "something1"}},
                            "max_purchase": {"market": {"name": "something2"}},
                            "listings": [{"market": {"name": "something3"}}],
                            "floor": [{"market": {"name": "something4"}}],
                        },
                    },
                    {
                        "value": "2.0",
                        "nft": {
                            "name": "foo2",
                            "max_purchase": {"market": {"name": "something5"}},
                            "listings": None,
                        },
                    },
                ],
            },
            {
                "value": "200",
                "amount": 20,
                "nfts": [
                    {
                        "value": "5.0",
                        "nft": {
                            "name": "foo5",
                            "max_purchase": {"market": {"name": "something9"}},
                            "floor": [{"market": {"name": "something10"}}],
                        },
                    }
                ],
            },
        ]
        returned = extract_nftcollections_headers(nftcollections)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == [
            {
                "value": "100",
                "amount": 10,
                "nfts": [
                    {
                        "value": "1.0",
                        "nft": {
                            "name": "foo1",
                            "urls": None,
                            "listings": None,
                            "floor": None,
                            "last_purchase": None,
                            "max_purchase": None,
                            "traits": None,
                        },
                    },
                    {
                        "value": "2.0",
                        "nft": {
                            "name": "foo2",
                            "urls": None,
                            "listings": None,
                            "floor": None,
                            "last_purchase": None,
                            "max_purchase": None,
                            "traits": None,
                        },
                    },
                ],
            },
            {
                "value": "200",
                "amount": 20,
                "nfts": [
                    {
                        "value": "5.0",
                        "nft": {
                            "name": "foo5",
                            "urls": None,
                            "listings": None,
                            "floor": None,
                            "last_purchase": None,
                            "max_purchase": None,
                            "traits": None,
                        },
                    },
                ],
            },
        ]

    # # extract_nftcollections_market
    def test_api_helpers_extract_nftcollections_market_for_no_market(self):
        market = ""
        nftcollections = [
            {
                "value": "1.0",
                "nfts": [
                    {
                        "value": "1.0",
                        "nft": {
                            "name": "foo1",
                            "last_purchase": {"market": {"name": "something1"}},
                            "max_purchase": {"market": {"name": "something2"}},
                            "listings": [{"market": {"name": "something3"}}],
                            "floor": [{"market": {"name": "something4"}}],
                        },
                    },
                    {
                        "value": "2.0",
                        "nft": {
                            "name": "foo2",
                            "max_purchase": {"market": {"name": "something5"}},
                            "listings": None,
                        },
                    },
                ],
            },
            {
                "value": "5.0",
                "nfts": [
                    {
                        "value": "5.0",
                        "nft": {
                            "name": "foo5",
                            "max_purchase": {"market": {"name": "something9"}},
                            "floor": [{"market": {"name": "something10"}}],
                        },
                    }
                ],
            },
        ]
        returned = extract_nftcollections_market(market, nftcollections)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_nftcollections_market_for_no_nftcollections(
        self, mocker
    ):
        market = "market"
        nftcollections = []
        mocked_filter = mocker.patch("api.helpers._filter_nfts_by_market")
        returned = extract_nftcollections_market(market, nftcollections)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []
        mocked_filter.assert_not_called()

    def test_api_helpers_extract_nftcollections_market_functionality(self, mocker):
        market = "market"
        nftcollections = [
            {
                "value": "1.0",
                "nfts": [
                    {
                        "value": "1.0",
                        "nft": {
                            "name": "foo1",
                            "last_purchase": {"market": {"name": "something1"}},
                            "max_purchase": {"market": {"name": "something2"}},
                            "listings": [{"market": {"name": "something3"}}],
                            "floor": [{"market": {"name": "something4"}}],
                        },
                    },
                    {
                        "value": "2.0",
                        "nft": {
                            "name": "foo2",
                            "max_purchase": {"market": {"name": "something5"}},
                            "listings": None,
                        },
                    },
                ],
            },
            {
                "value": "5.0",
                "nfts": [
                    {
                        "value": "5.0",
                        "nft": {
                            "name": "foo5",
                            "max_purchase": {"market": {"name": "something9"}},
                            "floor": [{"market": {"name": "something10"}}],
                        },
                    }
                ],
            },
        ]
        mocked_filter = mocker.patch(
            "api.helpers._filter_nfts_by_market",
            side_effect=[[], nftcollections[1].get("nfts")],
        )
        returned = extract_nftcollections_market(market, nftcollections)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == [nftcollections[1]]
        calls = [
            mocker.call(market, nftcollections[0].get("nfts")),
            mocker.call(market, nftcollections[1].get("nfts")),
        ]
        mocked_filter.assert_has_calls(calls, any_order=True)
        assert mocked_filter.call_count == 2

    # # extract_nftcollections_sale_type
    def test_api_helpers_extract_nftcollections_sale_type_for_no_sale_type(self):
        sale_type = ""
        nftcollections = [
            {
                "value": "1.0",
                "nfts": [
                    {
                        "value": "1.0",
                        "nft": {
                            "name": "foo1",
                            "last_purchase": {"sale_type": {"name": "something1"}},
                            "max_purchase": {"sale_type": {"name": "something2"}},
                            "listings": [{"sale_type": {"name": "something3"}}],
                            "floor": [{"sale_type": {"name": "something4"}}],
                        },
                    },
                    {
                        "value": "2.0",
                        "nft": {
                            "name": "foo2",
                            "max_purchase": {"sale_type": {"name": "something5"}},
                            "listings": None,
                        },
                    },
                ],
            },
            {
                "value": "5.0",
                "nfts": [
                    {
                        "value": "5.0",
                        "nft": {
                            "name": "foo5",
                            "max_purchase": {"sale_type": {"name": "something9"}},
                            "floor": [{"sale_type": {"name": "something10"}}],
                        },
                    }
                ],
            },
        ]
        returned = extract_nftcollections_sale_type(sale_type, nftcollections)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_nftcollections_sale_type_for_no_nftcollections(
        self, mocker
    ):
        sale_type = "purchase"
        nftcollections = []
        mocked_filter = mocker.patch("api.helpers._filter_nfts_by_sale_type")
        returned = extract_nftcollections_sale_type(sale_type, nftcollections)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []
        mocked_filter.assert_not_called()

    def test_api_helpers_extract_nftcollections_sale_type_functionality(self, mocker):
        sale_type = "purchase"
        nftcollections = [
            {
                "value": "1.0",
                "nfts": [
                    {
                        "value": "1.0",
                        "nft": {
                            "name": "foo1",
                            "listings": [{"sale_type": {"name": "something3"}}],
                            "floor": [{"sale_type": {"name": "something4"}}],
                        },
                    },
                    {
                        "value": "2.0",
                        "nft": {
                            "name": "foo2",
                            "max_purchase": {"sale_type": {"name": "something5"}},
                            "listings": None,
                        },
                    },
                ],
            },
            {
                "value": "5.0",
                "nfts": [
                    {
                        "value": "5.0",
                        "nft": {
                            "name": "foo5",
                            "floor": [{"sale_type": {"name": "something10"}}],
                        },
                    }
                ],
            },
        ]
        mocked_filter = mocker.patch(
            "api.helpers._filter_nfts_by_sale_type",
            side_effect=[nftcollections[0].get("nfts")[1], []],
        )
        returned = extract_nftcollections_sale_type(sale_type, nftcollections)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == [
            {**nftcollections[0], **{"nfts": nftcollections[0].get("nfts")[1]}}
        ]
        calls = [
            mocker.call(sale_type, nftcollections[0].get("nfts")),
            mocker.call(sale_type, nftcollections[1].get("nfts")),
        ]
        mocked_filter.assert_has_calls(calls, any_order=True)
        assert mocked_filter.call_count == 2

    # # extract_nftcollection
    def test_api_helpers_extract_nftcollection_for_no_nftcollections(self):
        collection = "collection"
        nftcollections = []
        returned = extract_nftcollection(collection, nftcollections)
        assert returned == {}

    def test_api_helpers_extract_nftcollection_for_no_collection(self):
        collection = ""
        nftcollections = [
            {
                "value": 100.0,
                "amount": 1,
                "name": "collection",
                "nfts": [{"nft": {"id": 100}}, {"nft": {"id": 200}}],
            }
        ]
        returned = extract_nftcollection(collection, nftcollections)
        assert returned == {}

    def test_api_helpers_extract_nftcollection_functionality(self):
        collection = "collection"
        nftcollections = [
            {
                "value": "100.0",
                "amount": 1,
                "name": "name1",
                "nfts": [
                    {"value": "10", "nft": {"id": 100, "name": "name2"}},
                    {"nft": {"id": 200, "name": "name3"}},
                ],
            },
            {
                "value": "100.0",
                "amount": 1,
                "name": collection,
                "nfts": [
                    {"value": "210", "nft": {"id": 100, "name": "name4"}},
                    {"nft": {"id": 500, "name": "name4"}},
                    {"value": "580", "nft": {"id": 800, "name": "name5"}},
                ],
            },
        ]
        returned = extract_nftcollection(collection, nftcollections)
        assert returned == nftcollections[1]

    # # extract_nftitem
    def test_api_helpers_extract_nftitem_for_no_nftcollections(self):
        nft_id = 505
        nftcollections = []
        returned = extract_nftitem(nft_id, nftcollections)
        assert returned == {}

    def test_api_helpers_extract_nftitem_for_no_nft_id(self):
        nft_id = 505
        nftcollections = [
            {
                "value": 100.0,
                "amount": 1,
                "nfts": [{"nft": {"id": 100}}, {"nft": {"id": 200}}],
            }
        ]
        returned = extract_nftitem(nft_id, nftcollections)
        assert returned == {}

    def test_api_helpers_extract_nftitem_functionality(self):
        nft_id = 505
        nftcollections = [
            {
                "value": "100.0",
                "amount": 1,
                "nfts": [
                    {"value": "10", "nft": {"id": 100, "name": "name2"}},
                    {"nft": {"id": 200, "name": "name3"}},
                ],
            },
            {
                "value": "100.0",
                "amount": 1,
                "nfts": [
                    {"value": "210", "nft": {"id": 100, "name": "name4"}},
                    {"nft": {"id": nft_id, "name": "name4"}},
                    {"value": "580", "nft": {"id": 800, "name": "name5"}},
                ],
            },
        ]
        returned = extract_nftitem(nft_id, nftcollections)
        assert returned == {"nft": {"id": nft_id, "name": "name4"}}

    # # extract_nftitems_from_nftcollections
    def test_api_helpers_extract_nftitems_from_nftcollections_for_no_nftcollections(
        self,
    ):
        nftcollections = []
        returned = extract_nftitems_from_nftcollections(nftcollections)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == []

    def test_api_helpers_extract_nftitems_from_nftcollections_functionality(self):
        nftcollections = [
            {
                "value": "100.0",
                "amount": 1,
                "nfts": [
                    {"value": "10", "nft": {"id": 100, "name": "name2"}},
                    {"nft": {"id": 200, "name": "name3"}},
                ],
            },
            {
                "value": "100.0",
                "amount": 1,
                "nfts": [
                    {"value": "210", "nft": {"id": 100, "name": "name4"}},
                    {"nft": {"id": 300, "name": "name4"}},
                    {"value": "580", "nft": {"id": 800, "name": "name5"}},
                ],
            },
        ]
        returned = extract_nftitems_from_nftcollections(nftcollections)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == [
            {"value": "10", "nft": {"id": 100, "name": "name2"}},
            {"nft": {"id": 200, "name": "name3"}},
            {"value": "210", "nft": {"id": 100, "name": "name4"}},
            {"nft": {"id": 300, "name": "name4"}},
            {"value": "580", "nft": {"id": 800, "name": "name5"}},
        ]

    # # extract_nftitems_headers
    def test_api_helpers_extract_nftitems_headers_functionality(self):
        nftitems = [
            {
                "value": "1.0",
                "nft": {
                    "name": "foo1",
                    "listings": [{"sale_type": {"name": "something3"}}],
                    "floor": [{"sale_type": {"name": "something4"}}],
                    "urls": [{"url": "http"}],
                    "last_purchase": None,
                },
                "amount": 1,
            },
            {
                "value": "2.0",
                "nft": {
                    "name": "foo2",
                    "max_purchase": {"sale_type": {"name": "something5"}},
                    "listings": None,
                    "traits": [
                        {"name": "BACKDROP", "value": "Ommetaphobia"},
                        {"name": "SKIN", "value": "Cheese"},
                    ],
                },
                "amount": 1,
            },
            {
                "value": "5.0",
                "nft": {
                    "name": "foo5",
                    "floor": [{"sale_type": {"name": "something10"}}],
                    "last_purchase": {"sale_type": {"name": "something5"}},
                },
                "amount": 1,
            },
        ]
        returned = extract_nftitems_headers(nftitems)
        assert isinstance(returned, types.GeneratorType)
        assert list(returned) == [
            {
                "value": "1.0",
                "nft": {
                    "name": "foo1",
                    "urls": None,
                    "listings": None,
                    "floor": None,
                    "last_purchase": None,
                    "max_purchase": None,
                    "traits": None,
                },
                "amount": 1,
            },
            {
                "value": "2.0",
                "nft": {
                    "name": "foo2",
                    "urls": None,
                    "listings": None,
                    "floor": None,
                    "last_purchase": None,
                    "max_purchase": None,
                    "traits": None,
                },
                "amount": 1,
            },
            {
                "value": "5.0",
                "nft": {
                    "name": "foo5",
                    "urls": None,
                    "listings": None,
                    "floor": None,
                    "last_purchase": None,
                    "max_purchase": None,
                    "traits": None,
                },
                "amount": 1,
            },
        ]

    # # extract_nftitems_market
    def test_api_helpers_extract_nftitems_market_functionality(self, mocker):
        market = "market"
        nftitems = mocker.MagicMock()
        mocked_filter = mocker.patch("api.helpers._filter_nfts_by_market")
        returned = extract_nftitems_market(market, nftitems)
        assert returned == mocked_filter.return_value
        mocked_filter.assert_called_once_with(market, nftitems)

    # # extract_nftitems_sale_type
    def test_api_helpers_extract_nftitems_sale_type_functionality(self, mocker):
        sale_type = "sale_type"
        nftitems = mocker.MagicMock()
        mocked_filter = mocker.patch("api.helpers._filter_nfts_by_sale_type")
        returned = extract_nftitems_sale_type(sale_type, nftitems)
        assert returned == mocked_filter.return_value
        mocked_filter.assert_called_once_with(sale_type, nftitems)


class TestApiHelpersExtractAccount:
    """Testing class for :py:mod:`api.helpers` account related extract functions."""

    # # _extract_account_markets
    def test_api_helpers_extract_account_markets_functionality(self):
        nftcollections = [
            {
                "name": "name1",
                "nfts": [
                    {
                        "value": "1.0",
                        "nft": {
                            "name": "foo1",
                            "last_purchase": {"market": {"name": "something1"}},
                            "max_purchase": {"market": {"name": "something2"}},
                            "listings": [{"market": {"name": "something3"}}],
                            "floor": [{"market": {"name": "something4"}}],
                        },
                    },
                    {
                        "value": "2.0",
                        "nft": {
                            "name": "foo2",
                            "max_purchase": {"market": {"name": "something3"}},
                            "listings": None,
                        },
                    },
                    {
                        "value": "3.0",
                        "nft": {
                            "name": "foo3",
                            "last_purchase": None,
                            "listings": [
                                {"market": {"name": "something2"}},
                                {"market": {"name": "something3"}},
                            ],
                            "floor": None,
                        },
                    },
                    {
                        "value": "4.0",
                        "nft": {
                            "name": "foo4",
                            "last_purchase": {"market": {"name": "something5"}},
                            "max_purchase": None,
                            "listings": None,
                        },
                    },
                    {
                        "value": "5.0",
                        "nft": {
                            "name": "foo5",
                            "max_purchase": {"market": {"name": "something1"}},
                            "floor": [{"market": {"name": "something6"}}],
                        },
                    },
                ],
            },
            {
                "name": "name1",
                "nfts": [
                    {
                        "value": "5.0",
                        "nft": {
                            "name": "foo5",
                            "max_purchase": {"market": {"name": "something7"}},
                            "floor": [{"market": {"name": "something2"}}],
                        },
                    },
                ],
            },
        ]
        returned = _extract_account_markets(nftcollections)
        assert returned == [
            {
                "name": "something1",
            },
            {
                "name": "something2",
            },
            {
                "name": "something3",
            },
            {
                "name": "something4",
            },
            {
                "name": "something5",
            },
            {
                "name": "something6",
            },
            {
                "name": "something7",
            },
        ]

    # # _extract_account_programs
    def test_api_helpers_extract_account_programs_functionality(self):
        asaitems = [
            {
                "id": 505,
                "programs": [
                    {"program": {"name": "program4", "foo": "bar"}},
                    {"program": {"name": "program2", "type": "type2"}},
                    {"program": {"name": "program1"}},
                ],
            },
            {
                "id": 506,
                "programs": [
                    {"program": {"name": "program4", "foo1": "bar"}},
                    {"program": {"name": "program3"}},
                ],
            },
            {
                "id": 507,
                "programs": [
                    {"program": {"name": "program2", "type": "type2"}},
                    {"program": {"name": "program5"}},
                ],
            },
        ]
        returned = _extract_account_programs(asaitems)
        assert returned == [
            {"name": "program1"},
            {"name": "program2", "type": "type2"},
            {"name": "program3"},
            {"name": "program4"},
            {"name": "program5"},
        ]

    # # _extract_account_providers
    def test_api_helpers_extract_account_providers_functionality(self):
        programs = [
            {"code": 505, "provider": {"name": "provider1"}},
            {"code": 506, "provider": {"name": "provider3"}},
            {"code": 507, "provider": {"name": "provider1"}},
            {"code": 508},
            {"code": 509, "provider": {"name": "provider2"}},
        ]
        returned = _extract_account_providers(programs)
        assert returned == [
            {"name": "provider1"},
            {"name": "provider2"},
            {"name": "provider3"},
        ]

    # # _remove_duplicated_dicts_and_sort_by_name
    def test_api_helpers_remove_duplicated_dicts_and_sort_by_name_functionality(self):
        items = [
            {"name": "program4"},
            {"name": "program2"},
            {"name": "program1"},
            {"name": "program2"},
            {"name": "program4"},
            {"name": "program1"},
            {"name": "program3"},
            {"name": "program1"},
            {"name": "program5"},
            {"name": "program2"},
        ]
        returned = _remove_duplicated_dicts_and_sort_by_name(items)
        assert returned == [
            {"name": "program1"},
            {"name": "program2"},
            {"name": "program3"},
            {"name": "program4"},
            {"name": "program5"},
        ]

    # # extract_account_entities
    def test_api_helpers_extract_account_entities_functionality(self, mocker):
        asaitems, nftcollections = mocker.MagicMock(), mocker.MagicMock()
        serialized_data = {"asaitems": asaitems, "nftcollections": nftcollections}
        mocked_programs = mocker.patch("api.helpers._extract_account_programs")
        mocked_providers = mocker.patch("api.helpers._extract_account_providers")
        mocked_markets = mocker.patch("api.helpers._extract_account_markets")
        returned = extract_account_entities(serialized_data)
        assert returned == {
            "programs": mocked_programs.return_value,
            "providers": mocked_providers.return_value,
            "markets": mocked_markets.return_value,
        }
        mocked_programs.assert_called_once_with(asaitems)
        mocked_providers.assert_called_once_with(mocked_programs.return_value)
        mocked_markets.assert_called_once_with(nftcollections)

    def test_api_helpers_extract_account_entities_for_no_items(self, mocker):
        serialized_data = {}
        mocked_programs = mocker.patch("api.helpers._extract_account_programs")
        mocked_providers = mocker.patch("api.helpers._extract_account_providers")
        mocked_markets = mocker.patch("api.helpers._extract_account_markets")
        returned = extract_account_entities(serialized_data)
        assert returned == {
            "programs": mocked_programs.return_value,
            "providers": mocked_providers.return_value,
            "markets": mocked_markets.return_value,
        }
        mocked_programs.assert_called_once_with([])
        mocked_providers.assert_called_once_with(mocked_programs.return_value)
        mocked_markets.assert_called_once_with([])

    # # extract_account_headers
    def test_api_helpers_extract_account_headers_functionality(self, mocker):
        asaitems, nftcollections = mocker.MagicMock(), mocker.MagicMock()
        serialized_data = {
            "foo": "bar",
            "asaitems": asaitems,
            "nftcollections": nftcollections,
            "foobar": "1",
        }
        mocked_asaitems = mocker.patch("api.helpers.extract_asaitems_headers")
        mocked_nftcollections = mocker.patch(
            "api.helpers.extract_nftcollections_headers"
        )
        returned = extract_account_headers(serialized_data)
        assert returned == {
            "foo": "bar",
            "asaitems": mocked_asaitems.return_value,
            "nftcollections": mocked_nftcollections.return_value,
            "foobar": "1",
        }
        mocked_asaitems.assert_called_once_with(asaitems)
        mocked_nftcollections.assert_called_once_with(nftcollections)

    # # extract_top_account_items
    def test_api_helpers_extract_top_account_items_for_too_large_limit(self, mocker):
        asaitems, nftcollections = [mocker.MagicMock()] * 2, [mocker.MagicMock()] * 5
        total, account_info = mocker.MagicMock(), mocker.MagicMock()
        serialized_data = {
            "total": total,
            "account_info": account_info,
            "system_info": mocker.MagicMock(),
            "asaitems": asaitems,
            "nftcollections": nftcollections,
            "notevals": mocker.MagicMock(),
        }
        limit = 8
        returned = extract_top_account_items(serialized_data, limit)
        assert returned == {
            "total": total,
            "account_info": account_info,
            "asaitems": asaitems,
            "nftcollections": nftcollections,
        }

    def test_api_helpers_extract_top_account_items_for_only_asaitems(self, mocker):
        asaitems = [
            {"value": "100", "amount": 1},
            {"value": "50", "amount": 1},
            {"value": "30", "amount": 1},
            {"value": "20", "amount": 1},
            {"value": "10", "amount": 1},
            {"value": "5", "amount": 1},
        ]
        nftcollections = [
            {"value": "4", "amount": 1},
            {"value": "3", "amount": 1},
            {"value": "2", "amount": 1},
            {"value": "1", "amount": 1},
        ]
        total, account_info = mocker.MagicMock(), mocker.MagicMock()
        serialized_data = {
            "total": total,
            "account_info": account_info,
            "system_info": mocker.MagicMock(),
            "asaitems": asaitems,
            "nftcollections": nftcollections,
            "notevals": mocker.MagicMock(),
        }
        limit = 5
        returned = extract_top_account_items(serialized_data, limit)
        assert returned == {
            "total": total,
            "account_info": account_info,
            "asaitems": asaitems[:limit],
            "nftcollections": [],
        }

    def test_api_helpers_extract_top_account_items_for_only_nftcollections(
        self, mocker
    ):
        asaitems = [
            {"value": "4", "amount": 1},
            {"value": "3", "amount": 1},
            {"value": "2", "amount": 1},
            {"value": "1", "amount": 1},
        ]
        nftcollections = [
            {"value": "100", "amount": 1},
            {"value": "50", "amount": 1},
            {"value": "30", "amount": 1},
            {"value": "20", "amount": 1},
            {"value": "10", "amount": 1},
            {"value": "5", "amount": 1},
        ]
        total, account_info = mocker.MagicMock(), mocker.MagicMock()
        serialized_data = {
            "total": total,
            "account_info": account_info,
            "system_info": mocker.MagicMock(),
            "asaitems": asaitems,
            "nftcollections": nftcollections,
            "notevals": mocker.MagicMock(),
        }
        limit = 5
        returned = extract_top_account_items(serialized_data, limit)
        assert returned == {
            "total": total,
            "account_info": account_info,
            "asaitems": [],
            "nftcollections": nftcollections[:limit],
        }

    def test_api_helpers_extract_top_account_items_for_account_without_nfts(
        self, mocker
    ):
        asaitems = [
            {"value": "100", "amount": 1},
            {"value": "50", "amount": 1},
            {"value": "30", "amount": 1},
            {"value": "20", "amount": 1},
            {"value": "10", "amount": 1},
            {"value": "5", "amount": 1},
        ]
        nftcollections = []
        total, account_info = mocker.MagicMock(), mocker.MagicMock()
        serialized_data = {
            "total": total,
            "account_info": account_info,
            "system_info": mocker.MagicMock(),
            "asaitems": asaitems,
            "nftcollections": nftcollections,
            "notevals": mocker.MagicMock(),
        }
        limit = 5
        returned = extract_top_account_items(serialized_data, limit)
        assert returned == {
            "total": total,
            "account_info": account_info,
            "asaitems": asaitems[:limit],
            "nftcollections": [],
        }

    def test_api_helpers_extract_top_account_items_functionality(self, mocker):
        asaitems = [
            {"value": "100", "amount": 1},
            {"value": "50", "amount": 1},
            {"value": "30", "amount": 1},
            {"value": "20", "amount": 1},
            {"value": "10", "amount": 1},
        ]
        nftcollections = [
            {"value": "54", "amount": 1},
            {"value": "33", "amount": 1},
            {"value": "22", "amount": 1},
            {"value": "11", "amount": 1},
        ]
        total, account_info = mocker.MagicMock(), mocker.MagicMock()
        serialized_data = {
            "total": total,
            "account_info": account_info,
            "system_info": mocker.MagicMock(),
            "asaitems": asaitems,
            "nftcollections": nftcollections,
            "notevals": mocker.MagicMock(),
        }
        limit = 5
        returned = extract_top_account_items(serialized_data, limit)
        assert returned == {
            "total": total,
            "account_info": account_info,
            "asaitems": [
                {"value": "100", "amount": 1},
                {"value": "50", "amount": 1},
                {"value": "30", "amount": 1},
            ],
            "nftcollections": [
                {"value": "54", "amount": 1},
                {"value": "33", "amount": 1},
            ],
        }


class TestApiHelpersValidation:
    """Testing class for :py:mod:`api.helpers` validation functions."""

    # # validate_address
    def test_api_helpers_validate_address_raises_validationerror_for_no_value(self):
        with pytest.raises(ValidationError) as exception:
            validate_address(None)
        assert (
            str(exception.value)
            == f"[ErrorDetail(string='{INVALID_ADDRESS_INPUT_TEXT}', code='invalid')]"
        )

    def test_api_helpers_validate_address_raises_validationerror_for_no_valid_address(
        self, mocker
    ):
        mocked_is_valid = mocker.patch(
            "api.helpers.is_valid_address", return_value=False
        )
        value = mocker.MagicMock()
        with pytest.raises(ValidationError) as exception:
            validate_address(value)
        assert (
            str(exception.value)
            == f"[ErrorDetail(string='{INVALID_ADDRESS_TEXT}', code='invalid')]"
        )
        mocked_is_valid.assert_called_once_with(value)

    def test_api_helpers_validate_address_functionality(self, mocker):
        mocked_is_valid = mocker.patch(
            "api.helpers.is_valid_address", return_value=True
        )
        value = mocker.MagicMock()
        returned = validate_address(value)
        assert returned == value
        mocked_is_valid.assert_called_once_with(value)

    # # validate_bundle
    def test_api_helpers_validate_bundle_raises_validationerror_for_no_value(
        self, mocker
    ):
        mocked_address = mocker.patch("api.helpers.validate_address")
        with pytest.raises(ValidationError) as exception:
            validate_bundle(None)
        assert (
            str(exception.value)
            == f"[ErrorDetail(string='{INVALID_INPUT_TEXT}', code='invalid')]"
        )
        mocked_address.assert_not_called()

    def test_api_helpers_validate_bundle_returns_validate_address_for_provided_address(
        self, mocker
    ):
        mocked_address = mocker.patch("api.helpers.validate_address")
        mocked_check = mocker.patch("api.helpers.check_bundle_addresses")
        value = API_EXAMPLE_ADDRESS1
        returned = validate_bundle(value)
        assert returned == mocked_address.return_value
        mocked_address.assert_called_once_with(value)
        mocked_check.assert_not_called()

    def test_api_helpers_validate_bundle_raises_validationerror_for_no_addresses(
        self, mocker
    ):
        mocked_address = mocker.patch("api.helpers.validate_address")
        mocked_check = mocker.patch(
            "api.helpers.check_bundle_addresses", return_value=""
        )
        value = API_EXAMPLE_BUNDLE1
        with pytest.raises(ValidationError) as exception:
            validate_bundle(value)
        assert (
            str(exception.value)
            == f"""[ErrorDetail(string="{INVALID_BUNDLE_TEXT}", code='invalid')]"""
        )
        mocked_check.assert_called_once_with(value)
        mocked_address.assert_not_called()

    def test_api_helpers_validate_bundle_functionality(self, mocker):
        mocked_address = mocker.patch("api.helpers.validate_address")
        mocked_check = mocker.patch(
            "api.helpers.check_bundle_addresses", return_value="afddresses"
        )
        value = API_EXAMPLE_BUNDLE1
        returned = validate_bundle(value)
        assert returned == value
        mocked_check.assert_called_once_with(value)
        mocked_address.assert_not_called()

    # # validate_nfd_name
    def test_api_helpers_validate_nfd_name_raises_validationerror_for_no_nfd_name(
        self, mocker
    ):
        mocked_check = mocker.patch("api.helpers.check_algorand_address")
        with pytest.raises(ValidationError) as exception:
            validate_nfd_name(None)
        assert (
            str(exception.value)
            == f"[ErrorDetail(string='{INVALID_NFD_NAME_TEXT}', code='invalid')]"
        )
        mocked_check.assert_not_called()

    def test_api_helpers_validate_nfd_name_raises_validationerror_for_no_addresses(
        self, mocker
    ):
        mocked_check = mocker.patch(
            "api.helpers.check_algorand_address", return_value=False
        )
        mocked_create = mocker.patch("api.helpers.create_bundle")
        nfd_name = API_EXAMPLE_BUNDLE1
        with pytest.raises(ValidationError) as exception:
            validate_nfd_name(nfd_name)
        assert (
            str(exception.value)
            == f"[ErrorDetail(string='{INVALID_NFD_NAME_TEXT}', code='invalid')]"
        )
        mocked_check.assert_called_once_with(nfd_name, raise_error=True)
        mocked_create.assert_not_called()

    def test_api_helpers_validate_nfd_name_for_bundle(self, mocker):
        addresses = f"{API_EXAMPLE_ADDRESS1} {API_EXAMPLE_ADDRESS2}"
        mocked_check = mocker.patch(
            "api.helpers.check_algorand_address", return_value=addresses
        )
        mocked_create = mocker.patch("api.helpers.create_bundle")
        nfd_name = API_EXAMPLE_BUNDLE1
        returned = validate_nfd_name(nfd_name)
        assert returned == mocked_create.return_value
        mocked_check.assert_called_once_with(nfd_name, raise_error=True)
        mocked_create.assert_called_once_with(addresses)

    def test_api_helpers_validate_nfd_name_for_single_address(self, mocker):
        addresses = API_EXAMPLE_ADDRESS1
        mocked_check = mocker.patch(
            "api.helpers.check_algorand_address", return_value=addresses
        )
        mocked_create = mocker.patch("api.helpers.create_bundle")
        nfd_name = API_EXAMPLE_BUNDLE1
        returned = validate_nfd_name(nfd_name)
        assert returned == addresses
        mocked_check.assert_called_once_with(nfd_name, raise_error=True)
        mocked_create.assert_not_called()

    # # validate_raw_addresses
    def test_api_helpers_validate_raw_addresses_raises_validationerror_for_no_raw(
        self, mocker
    ):
        mocked_address = mocker.patch("api.helpers.validate_address")
        with pytest.raises(ValidationError) as exception:
            validate_raw_addresses(None)
        assert (
            str(exception.value)
            == f"[ErrorDetail(string='{INVALID_RAW_TEXT}', code='invalid')]"
        )
        mocked_address.assert_not_called()

    def test_api_helpers_validate_raw_addresses_returns_check_for_address(self, mocker):
        mocked_check = mocker.patch("api.helpers.check_algorand_address")
        mocked_normalize = mocker.patch("api.helpers._normalize_collection")
        mocked_parse = mocker.patch("api.helpers._parse_bundle")
        raw = API_EXAMPLE_ADDRESS1
        returned = validate_raw_addresses(raw)
        assert returned == mocked_check.return_value
        mocked_check.assert_called_once_with(raw, raise_error=True)
        mocked_normalize.assert_not_called()
        mocked_parse.assert_not_called()

    def test_api_helpers_validate_raw_addresses_raises_validationerror_for_no_addresses(
        self, mocker
    ):
        mocked_check = mocker.patch("api.helpers.check_algorand_address")
        mocked_normalize = mocker.patch(
            "api.helpers._normalize_collection", return_value=False
        )
        mocked_parse = mocker.patch("api.helpers._parse_bundle")
        raw = API_EXAMPLE_BUNDLE1
        with pytest.raises(ValidationError) as exception:
            validate_raw_addresses(raw)
        assert (
            str(exception.value)
            == f"[ErrorDetail(string='{INVALID_RAW_TEXT}', code='invalid')]"
        )
        mocked_parse.assert_called_once_with(raw)
        mocked_normalize.assert_called_once_with(mocked_parse.return_value)
        mocked_check.assert_not_called()

    def test_api_helpers_validate_raw_addresses_functionality(self, mocker):
        mocked_check = mocker.patch("api.helpers.check_algorand_address")
        collection = [API_EXAMPLE_ADDRESS1, "", API_EXAMPLE_ADDRESS2]
        mocked_normalize = mocker.patch(
            "api.helpers._normalize_collection", return_value=collection
        )
        mocked_parse = mocker.patch("api.helpers._parse_bundle")
        raw = API_EXAMPLE_BUNDLE1
        returned = validate_raw_addresses(raw)
        assert returned in (
            f"{API_EXAMPLE_ADDRESS1} {API_EXAMPLE_ADDRESS2}",
            f"{API_EXAMPLE_ADDRESS2} {API_EXAMPLE_ADDRESS1}",
        )
        mocked_parse.assert_called_once_with(raw)
        mocked_normalize.assert_called_once_with(mocked_parse.return_value)
        mocked_check.assert_not_called()


class TestApiHelpersCustomSetings:
    """Testing class for :py:mod:`api.helpers` custom settings functions."""

    # # get_lib_doc_excludes
    def test_api_helpers_get_lib_doc_excludes_functionality(self):
        returned = get_lib_doc_excludes()
        assert returned == [
            object,
            *[
                getattr(api.serializers, c)
                for c in dir(api.serializers)
                if c.endswith("Serializer")
            ],
        ]

    # # preprocessing_filter_spec
    def test_api_helpers_preprocessing_filter_spec_functionality(self, mocker):
        path_regex1, method1, callback1 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        path_regex2, method2, callback2 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        path_regex3, method3, callback3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        path1 = "/api/v2/schema/redoc"
        path2 = "/api/v2/schema/"
        path3 = "/api/v2/"
        endpoints1 = [path1, path_regex1, method1, callback1]
        endpoints2 = [path2, path_regex2, method2, callback2]
        endpoints3 = [path3, path_regex3, method3, callback3]

        returned = preprocessing_filter_spec([endpoints1, endpoints2, endpoints3])
        assert returned == [tuple(endpoints1), tuple(endpoints3)]
