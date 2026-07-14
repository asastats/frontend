"""Testing module for :py:mod:`api.main` module."""

from api.data import API_EXAMPLE_ADDRESS1, API_EXAMPLE_BUNDLE1
from api.main import (
    account_entities,
    fetch_and_serialize_account,
    filtered_asaitem,
    filtered_nftcollection,
    filtered_nftitem,
    processed_account,
    processed_asaitems,
    processed_nftcollections,
    processed_nftitems,
)


class TestApMainFunctions:
    """Testing class for :py:mod:`api.main` functions."""

    # # account_entities
    def test_api_main_account_entities_functionality(self, mocker):
        serialized_data = mocker.MagicMock()
        mocked_extract = mocker.patch("api.main.extract_account_entities")
        returned = account_entities(serialized_data)
        assert returned == mocked_extract.return_value
        mocked_extract.assert_called_once_with(serialized_data)

    # # fetch_and_serialize_account
    def test_api_main_fetch_and_serialize_account_functionality(self, mocker):
        value, addresses = API_EXAMPLE_BUNDLE1, "FOO BAR"
        mocked_bundle = mocker.patch("api.main.bundle_from_addresses")
        mocked_fetch = mocker.patch("api.main.fetch_serialized_account")
        returned = fetch_and_serialize_account(value, addresses)
        assert returned == mocked_fetch.return_value
        mocked_fetch.assert_called_once_with(mocked_bundle.return_value, addresses)

    def test_api_main_fetch_and_serialize_account_for_single_address(self, mocker):
        value = API_EXAMPLE_ADDRESS1
        mocked_bundle = mocker.patch("api.main.bundle_from_addresses")
        mocked_fetch = mocker.patch("api.main.fetch_serialized_account")
        returned = fetch_and_serialize_account(value, value)
        assert returned == mocked_fetch.return_value
        mocked_fetch.assert_called_once_with(value, value)
        mocked_bundle.assert_not_called()

    # # filtered_asaitem
    def test_api_main_filtered_asaitem_for_usd(self, mocker):
        asset_id = mocker.MagicMock()
        asaitems = mocker.MagicMock()
        pricealgo = mocker.MagicMock()
        serialized_data = {
            "asaitems": asaitems,
            "total": {"pricealgo": pricealgo},
        }
        query_params = {"usd": "true"}
        asaitem = mocker.MagicMock()
        mocked_extract = mocker.patch("api.main.extract_asaitem", return_value=asaitem)
        converted = mocker.MagicMock()
        mocked_convert = mocker.patch(
            "api.main.convert_asaitems_values_to_usd", return_value=[converted]
        )
        returned = filtered_asaitem(asset_id, serialized_data, query_params)
        assert returned == converted
        mocked_extract.assert_called_once_with(asset_id, asaitems)
        mocked_convert.assert_called_once_with([asaitem], pricealgo)

    def test_api_main_filtered_asaitem_functionality(self, mocker):
        asset_id = mocker.MagicMock()
        asaitems = mocker.MagicMock()
        serialized_data = {"asaitems": asaitems}
        query_params = {"foo": "true"}
        asaitem = mocker.MagicMock()
        mocked_extract = mocker.patch("api.main.extract_asaitem", return_value=asaitem)
        mocked_convert = mocker.patch("api.main.convert_asaitems_values_to_usd")
        returned = filtered_asaitem(asset_id, serialized_data, query_params)
        assert returned == asaitem
        mocked_extract.assert_called_once_with(asset_id, asaitems)
        mocked_convert.assert_not_called()

    # # filtered_nftcollection
    def test_api_main_filtered_nftcollection_for_usd(self, mocker):
        collection = mocker.MagicMock()
        nftcollections = mocker.MagicMock()
        pricealgo = mocker.MagicMock()
        serialized_data = {
            "nftcollections": nftcollections,
            "total": {"pricealgo": pricealgo},
        }
        query_params = {"usd": "true"}
        nftcollection = mocker.MagicMock()
        mocked_extract = mocker.patch(
            "api.main.extract_nftcollection", return_value=nftcollection
        )
        converted = mocker.MagicMock()
        mocked_convert = mocker.patch(
            "api.main.convert_nftcollections_values_to_usd", return_value=[converted]
        )
        returned = filtered_nftcollection(collection, serialized_data, query_params)
        assert returned == converted
        mocked_extract.assert_called_once_with(collection, nftcollections)
        mocked_convert.assert_called_once_with([nftcollection], pricealgo)

    def test_api_main_filtered_nftcollection_functionality(self, mocker):
        collection = mocker.MagicMock()
        nftcollections = mocker.MagicMock()
        serialized_data = {"nftcollections": nftcollections}
        query_params = {"foo": "true"}
        nftcollection = mocker.MagicMock()
        mocked_extract = mocker.patch(
            "api.main.extract_nftcollection", return_value=nftcollection
        )
        mocked_convert = mocker.patch("api.main.convert_nftcollections_values_to_usd")
        returned = filtered_nftcollection(collection, serialized_data, query_params)
        assert returned == nftcollection
        mocked_extract.assert_called_once_with(collection, nftcollections)
        mocked_convert.assert_not_called()

    # # filtered_nftitem
    def test_api_main_filtered_nftitem_for_usd(self, mocker):
        nft_id = mocker.MagicMock()
        nftcollections = mocker.MagicMock()
        pricealgo = mocker.MagicMock()
        serialized_data = {
            "nftcollections": nftcollections,
            "total": {"pricealgo": pricealgo},
        }
        query_params = {"usd": "true"}
        nftitem = mocker.MagicMock()
        mocked_extract = mocker.patch("api.main.extract_nftitem", return_value=nftitem)
        converted = mocker.MagicMock()
        mocked_convert = mocker.patch(
            "api.main.convert_items_values_to_usd", return_value=[converted]
        )
        returned = filtered_nftitem(nft_id, serialized_data, query_params)
        assert returned == converted
        mocked_extract.assert_called_once_with(nft_id, nftcollections)
        mocked_convert.assert_called_once_with([nftitem], pricealgo)

    def test_api_main_filtered_nftitem_functionality(self, mocker):
        nft_id = mocker.MagicMock()
        nftcollections = mocker.MagicMock()
        serialized_data = {"nftcollections": nftcollections}
        query_params = {"foo": "true"}
        nftitem = mocker.MagicMock()
        mocked_extract = mocker.patch("api.main.extract_nftitem", return_value=nftitem)
        mocked_convert = mocker.patch("api.main.convert_items_values_to_usd")
        returned = filtered_nftitem(nft_id, serialized_data, query_params)
        assert returned == nftitem
        mocked_extract.assert_called_once_with(nft_id, nftcollections)
        mocked_convert.assert_not_called()

    # # processed_account
    def test_api_main_processed_account_for_no_query_params(self, mocker):
        serialized_data = mocker.MagicMock()
        query_params = {}
        mocked_top = mocker.patch("api.main.extract_top_account_items")
        mocked_headers = mocker.patch("api.main.extract_account_headers")
        mocked_convert = mocker.patch("api.main.convert_account_values_to_usd")
        returned = processed_account(serialized_data, query_params)
        assert returned == serialized_data
        mocked_top.assert_not_called()
        mocked_headers.assert_not_called()
        mocked_convert.assert_not_called()

    def test_api_main_processed_account_for_limit_0(self, mocker):
        serialized_data = mocker.MagicMock()
        query_params = {"limit": "0", "headers": "false"}
        mocked_top = mocker.patch("api.main.extract_top_account_items")
        mocked_headers = mocker.patch("api.main.extract_account_headers")
        mocked_convert = mocker.patch("api.main.convert_account_values_to_usd")
        returned = processed_account(serialized_data, query_params)
        assert returned == mocked_top.return_value
        mocked_top.assert_called_once_with(serialized_data, 0)
        mocked_headers.assert_not_called()
        mocked_convert.assert_not_called()

    def test_api_main_processed_account_functionality(self, mocker):
        serialized_data = mocker.MagicMock()
        query_params = {
            "limit": "10",
            "headers": "true",
            "usd": "true",
        }
        mocked_top = mocker.patch("api.main.extract_top_account_items")
        pricealgo = mocker.MagicMock()
        headers_serialized_data = {"foo": "bar", "total": {"pricealgo": pricealgo}}
        mocked_headers = mocker.patch(
            "api.main.extract_account_headers", return_value=headers_serialized_data
        )
        mocked_convert = mocker.patch("api.main.convert_account_values_to_usd")
        returned = processed_account(serialized_data, query_params)
        assert returned == mocked_convert.return_value
        mocked_top.assert_called_once_with(serialized_data, 10)
        mocked_headers.assert_called_once_with(mocked_top.return_value)
        mocked_convert.assert_called_once_with(headers_serialized_data, pricealgo)

    # # processed_asaitems
    def test_api_main_processed_asaitems_for_no_query_params(self, mocker):
        asaitems = mocker.MagicMock()
        serialized_data = {"asaitems": asaitems}
        query_params = {}
        mocked_provider = mocker.patch("api.main.extract_asaitems_provider")
        mocked_program = mocker.patch("api.main.extract_asaitems_program")
        mocked_type = mocker.patch("api.main.extract_asaitems_program_type")
        mocked_headers = mocker.patch("api.main.extract_asaitems_headers")
        mocked_convert = mocker.patch("api.main.convert_asaitems_values_to_usd")
        returned = processed_asaitems(serialized_data, query_params)
        assert returned == asaitems
        mocked_provider.assert_not_called()
        mocked_program.assert_not_called()
        mocked_type.assert_not_called()
        mocked_headers.assert_not_called()
        mocked_convert.assert_not_called()

    def test_api_main_processed_asaitems_for_limit_0(self, mocker):
        asaitems = mocker.MagicMock()
        serialized_data = {"asaitems": asaitems}
        query_params = {"limit": "0", "headers": "false"}
        mocked_provider = mocker.patch("api.main.extract_asaitems_provider")
        mocked_program = mocker.patch("api.main.extract_asaitems_program")
        mocked_type = mocker.patch("api.main.extract_asaitems_program_type")
        mocked_headers = mocker.patch("api.main.extract_asaitems_headers")
        mocked_convert = mocker.patch("api.main.convert_asaitems_values_to_usd")
        returned = processed_asaitems(serialized_data, query_params)
        assert returned == asaitems
        mocked_provider.assert_not_called()
        mocked_program.assert_not_called()
        mocked_type.assert_not_called()
        mocked_headers.assert_not_called()
        mocked_convert.assert_not_called()

    def test_api_main_processed_asaitems_functionality(self, mocker):
        asaitems = mocker.MagicMock()
        pricealgo = mocker.MagicMock()
        serialized_data = {"asaitems": asaitems, "total": {"pricealgo": pricealgo}}
        query_params = {
            "provider": "provider",
            "program": "program",
            "type": "type",
            "limit": "10",
            "headers": "true",
            "usd": "true",
        }
        mocked_provider = mocker.patch("api.main.extract_asaitems_provider")
        mocked_program = mocker.patch("api.main.extract_asaitems_program")
        asaitems_type = [mocker.MagicMock() * 50]
        mocked_type = mocker.patch(
            "api.main.extract_asaitems_program_type", return_value=asaitems_type
        )
        mocked_headers = mocker.patch("api.main.extract_asaitems_headers")
        mocked_convert = mocker.patch("api.main.convert_asaitems_values_to_usd")
        returned = processed_asaitems(serialized_data, query_params)
        assert returned == mocked_convert.return_value
        mocked_provider.assert_called_once_with("provider", asaitems)
        mocked_program.assert_called_once_with("program", mocked_provider.return_value)
        mocked_type.assert_called_once_with("type", mocked_program.return_value)
        mocked_headers.assert_called_once_with(asaitems_type[:10])
        mocked_convert.assert_called_once_with(mocked_headers.return_value, pricealgo)

    # # processed_nftcollections
    def test_api_main_processed_nftcollections_for_no_query_params(self, mocker):
        nftcollections = mocker.MagicMock()
        serialized_data = {"nftcollections": nftcollections}
        query_params = {}
        mocked_market = mocker.patch("api.main.extract_nftcollections_market")
        mocked_type = mocker.patch("api.main.extract_nftcollections_sale_type")
        mocked_headers = mocker.patch("api.main.extract_nftcollections_headers")
        mocked_convert = mocker.patch("api.main.convert_nftcollections_values_to_usd")
        returned = processed_nftcollections(serialized_data, query_params)
        assert returned == nftcollections
        mocked_market.assert_not_called()
        mocked_type.assert_not_called()
        mocked_headers.assert_not_called()
        mocked_convert.assert_not_called()

    def test_api_main_processed_nftcollections_for_limit_0(self, mocker):
        nftcollections = mocker.MagicMock()
        serialized_data = {"nftcollections": nftcollections}
        query_params = {"limit": "0", "headers": "false"}
        mocked_market = mocker.patch("api.main.extract_nftcollections_market")
        mocked_type = mocker.patch("api.main.extract_nftcollections_sale_type")
        mocked_headers = mocker.patch("api.main.extract_nftcollections_headers")
        mocked_convert = mocker.patch("api.main.convert_nftcollections_values_to_usd")
        returned = processed_nftcollections(serialized_data, query_params)
        assert returned == nftcollections
        mocked_market.assert_not_called()
        mocked_type.assert_not_called()
        mocked_headers.assert_not_called()
        mocked_convert.assert_not_called()

    def test_api_main_processed_nftcollections_functionality(self, mocker):
        nftcollections = mocker.MagicMock()
        pricealgo = mocker.MagicMock()
        serialized_data = {
            "nftcollections": nftcollections,
            "total": {"pricealgo": pricealgo},
        }
        query_params = {
            "market": "market",
            "type": "type",
            "limit": "10",
            "headers": "true",
            "usd": "true",
        }
        mocked_market = mocker.patch("api.main.extract_nftcollections_market")
        nftcollections_type = [mocker.MagicMock() * 50]
        mocked_type = mocker.patch(
            "api.main.extract_nftcollections_sale_type",
            return_value=nftcollections_type,
        )
        mocked_headers = mocker.patch("api.main.extract_nftcollections_headers")
        mocked_convert = mocker.patch("api.main.convert_nftcollections_values_to_usd")
        returned = processed_nftcollections(serialized_data, query_params)
        assert returned == mocked_convert.return_value
        mocked_market.assert_called_once_with("market", nftcollections)
        mocked_type.assert_called_once_with("type", mocked_market.return_value)
        mocked_headers.assert_called_once_with(nftcollections_type[:10])
        mocked_convert.assert_called_once_with(mocked_headers.return_value, pricealgo)

    # # processed_nftitems
    def test_api_main_processed_nftitems_for_no_query_params(self, mocker):
        nftcollections = mocker.MagicMock()
        serialized_data = {"nftcollections": nftcollections}
        query_params = {}
        mocked_nftitems = mocker.patch(
            "api.main.extract_nftitems_from_nftcollections",
            return_value=[
                {"value": "10.1"},
                {"value": "100.1"},
                {"value": "40.8"},
                {"value": "0.1"},
                {"value": "1000"},
                {"value": "5.0"},
                {"value": "250.40"},
            ],
        )
        mocked_market = mocker.patch("api.main.extract_nftitems_market")
        mocked_type = mocker.patch("api.main.extract_nftitems_sale_type")
        mocked_headers = mocker.patch("api.main.extract_nftitems_headers")
        mocked_convert = mocker.patch("api.main.convert_items_values_to_usd")
        returned = processed_nftitems(serialized_data, query_params)
        assert returned == [
            {"value": "1000"},
            {"value": "250.40"},
            {"value": "100.1"},
            {"value": "40.8"},
            {"value": "10.1"},
            {"value": "5.0"},
            {"value": "0.1"},
        ]
        mocked_nftitems.assert_called_once_with(nftcollections)
        mocked_market.assert_not_called()
        mocked_type.assert_not_called()
        mocked_headers.assert_not_called()
        mocked_convert.assert_not_called()

    def test_api_main_processed_nftitems_for_limit_0(self, mocker):
        nftcollections = mocker.MagicMock()
        serialized_data = {"nftcollections": nftcollections}
        query_params = {"limit": "0", "headers": "false"}
        mocked_nftitems = mocker.patch(
            "api.main.extract_nftitems_from_nftcollections",
            return_value=[
                {"value": "10.1"},
                {"value": "100.1"},
                {"value": "40.8"},
                {"value": "0.1"},
                {"value": "1000"},
                {"value": "5.0"},
                {"value": "250.40"},
            ],
        )
        mocked_market = mocker.patch("api.main.extract_nftitems_market")
        mocked_type = mocker.patch("api.main.extract_nftitems_sale_type")
        mocked_headers = mocker.patch("api.main.extract_nftitems_headers")
        mocked_convert = mocker.patch("api.main.convert_items_values_to_usd")
        returned = processed_nftitems(serialized_data, query_params)
        assert returned == [
            {"value": "1000"},
            {"value": "250.40"},
            {"value": "100.1"},
            {"value": "40.8"},
            {"value": "10.1"},
            {"value": "5.0"},
            {"value": "0.1"},
        ]
        mocked_nftitems.assert_called_once_with(nftcollections)
        mocked_market.assert_not_called()
        mocked_type.assert_not_called()
        mocked_headers.assert_not_called()
        mocked_convert.assert_not_called()

    def test_api_main_processed_nftitems_functionality(self, mocker):
        nftcollections = mocker.MagicMock()
        pricealgo = mocker.MagicMock()
        serialized_data = {
            "nftcollections": nftcollections,
            "total": {"pricealgo": pricealgo},
        }
        query_params = {
            "market": "market",
            "type": "type",
            "limit": "5",
            "headers": "true",
            "usd": "true",
        }
        mocked_nftitems = mocker.patch("api.main.extract_nftitems_from_nftcollections")
        mocked_market = mocker.patch("api.main.extract_nftitems_market")
        mocked_type = mocker.patch("api.main.extract_nftitems_sale_type")
        nftitems_headers = [
            {"value": "10.1"},
            {"value": "100.1"},
            {"value": "40.8"},
            {"value": "0.1"},
            {"value": "1000"},
            {"value": "5.0"},
            {"value": "250.40"},
        ]
        mocked_headers = mocker.patch(
            "api.main.extract_nftitems_headers",
            return_value=nftitems_headers,
        )
        mocked_convert = mocker.patch("api.main.convert_items_values_to_usd")
        returned = processed_nftitems(serialized_data, query_params)
        assert returned == mocked_convert.return_value
        mocked_nftitems.assert_called_once_with(nftcollections)
        mocked_market.assert_called_once_with("market", mocked_nftitems.return_value)
        mocked_type.assert_called_once_with("type", mocked_market.return_value)
        mocked_headers.assert_called_once_with(mocked_type.return_value)
        mocked_convert.assert_called_once_with(
            [
                {"value": "1000"},
                {"value": "250.40"},
                {"value": "100.1"},
                {"value": "40.8"},
                {"value": "10.1"},
            ],
            pricealgo,
        )
