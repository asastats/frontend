"""Testing module for :py:mod:`utils.charts` module's cosolidated view functions."""

from collections import namedtuple
from unittest import mock

import pytest

from utils.charts import (
    _asa_chart_from_serialized_data,
    _balance_totals_from_assets_data,
    _balance_totals_from_serialized_data,
    _base_chart_data_from_serialized_data,
    _consolidated_data_from_assets_data,
    _consolidated_data_from_serialized_data,
    _consolidated_totals_from_consolidated_data,
    _defi_totals_from_assets_data,
    _defi_totals_from_serialized_data,
    _distribution_chart_data_from_serialized_data,
    _distribution_chart_from_serialized_data,
    _liquidity_totals_from_assets_data,
    _liquidity_totals_from_serialized_data,
    _nft_chart_from_serialized_data,
    _nftfloor_totals_from_serialized_data,
    _staked_totals_from_assets_data,
    _staked_totals_from_serialized_data,
    _total_from_serialized_data,
    _unit_for_asaitem,
    prepare_consolidated_charts,
    prepare_consolidated_charts_from_assets_data,
    prepare_consolidated_charts_from_serialized_data,
)
from utils.constants.charts import (
    ASASTATS_COLOR_OTHERS,
    DISTINCT_COLORS,
    DISTINCT_COLORS_2,
    DISTRIBUTION_COLORS,
)
from utils.structs import Consolidated, Total


# # FIXTURES
def _asaitem(value, asset_id, unit, amount=0, decimals=6, programs=None):
    """Build a minimal serialized asaitem in the shape produced by api.serializers."""
    return {
        "value": str(value),
        "asset": {
            "id": asset_id,
            "name": unit,
            "unit": unit,
            "decimals": decimals,
        },
        "amount": amount,
        "programs": programs or [],
    }


def _nftcollection(value, name, amount=1, nfts=None):
    """Build a minimal serialized nftcollection."""
    return {
        "value": str(value),
        "name": name,
        "amount": amount,
        "nfts": nfts or [],
    }


class TestUtilsChartConsolidatedFunctions:
    """Testing class for :py:mod:`utils.charts` consolidated view functions."""

    def _mocked_elem(self, typ, name, value, mocker, source=None):
        elem = mocker.MagicMock()
        elem.type = typ
        elem.name = name
        elem.value = value
        elem.source = source
        return elem

    # # _asa_chart_from_serialized_data
    def test_utils_charts_asa_chart_from_serialized_data_passes_empty_list(
        self, mocker
    ):
        mocked_base = mocker.patch(
            "utils.charts._base_chart_data_from_serialized_data",
            return_value={},
        )
        _asa_chart_from_serialized_data({}, {})
        mocked_base.assert_called_once_with([], {})

    def test_utils_charts_asa_chart_from_serialized_data_functionality(self, mocker):
        mocked_setup = mocker.patch("utils.charts._chart_setup")
        mocked_base = mocker.patch(
            "utils.charts._base_chart_data_from_serialized_data",
            return_value={"labels": ["X"], "data": ["100.0"], "colors": ["#000"]},
        )
        serialized_data = {"asaitems": [{"sentinel": True}]}
        asa_colors = {}
        returned = _asa_chart_from_serialized_data(serialized_data, asa_colors)
        assert returned == mocked_setup.return_value
        mocked_base.assert_called_once_with([{"sentinel": True}], asa_colors)
        mocked_setup.assert_called_once_with(
            "ASA data",
            labels=["X"],
            data=["100.0"],
            colors=["#000"],
        )

    # # _balance_totals_from_assets_data
    def test_utils_charts_balance_totals_from_assets_data_functionality(self, mocker):
        asset_id1, asset_id2, asset_id3, asset_id4 = 505, 506, 507, 508
        elem1 = self._mocked_elem("Staked", "Some farm", 800, mocker)
        elem2 = self._mocked_elem("Balance", "name2", 700, mocker)
        elem3 = self._mocked_elem("Staked", "name3", 600, mocker)
        elem4 = self._mocked_elem("Deposit", "name4", 500, mocker)
        elem5 = self._mocked_elem("Staked", "Liquidity", 400, mocker)
        elem6 = self._mocked_elem("Staked", "Liquidity", 1800, mocker)
        elem7 = self._mocked_elem(None, "name7", 1900, mocker)
        elem8 = self._mocked_elem("Balance", "name8", 2000, mocker)
        elem9 = self._mocked_elem("Staked", "Cometa farming", 2100, mocker)
        elem10 = self._mocked_elem("Added", "Staked", 2200, mocker)
        elem11 = self._mocked_elem("Staked", "Humble farm", 2300, mocker)
        elem12 = self._mocked_elem("Staked", "Liquidity", 500, mocker)
        body1 = [elem1, elem2, elem3, elem4, elem5]
        body2 = [elem6, elem7, elem8, elem9, elem10, elem11]
        body3 = [elem12]
        body4 = []
        info1, info2, info3, info4 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        info1.id = asset_id1
        info2.id = asset_id2
        info3.id = asset_id3
        info4.id = asset_id4
        assets_data = {
            "asa": [
                {"info": info1, "body": body1},
                {"info": info2, "body": body2},
                {"info": info3, "body": body3},
                {"info": info4, "body": body4},
            ]
        }
        returned = _balance_totals_from_assets_data(assets_data)
        assert returned == {
            asset_id1: 700.0,
            asset_id2: 2000.0,
            asset_id3: 0.0,
            asset_id4: 0.0,
        }

    # # _balance_totals_from_serialized_data
    def test_utils_charts_balance_totals_from_serialized_data_functionality(self):
        asset_id1, asset_id2, asset_id3, asset_id4 = 505, 506, 507, 508
        asaitems = [
            {
                "asset": {"id": asset_id1},
                "programs": [
                    {"program": {"name": "program4", "foo": "bar"}},
                    {"program": {"name": "program2", "type": "Balance"}, "value": 1000},
                    {"program": {"name": "program1"}},
                    {"program": {"name": "program8", "type": "Balance"}, "value": 2000},
                ],
            },
            {
                "asset": {"id": asset_id2},
                "programs": [
                    {"program": {"name": "program4", "type": "bar"}, "value": 100},
                    {"program": {"name": "program3"}, "value": 200},
                    {"program": {"name": "program2", "type": "Balance"}},
                ],
            },
            {
                "asset": {"id": asset_id3},
                "programs": [
                    {"program": {"name": "program2", "type": "Balance"}, "value": 500},
                    {"program": {"name": "program5"}},
                ],
            },
            {"asset": {"id": asset_id4}},
        ]
        serialized_data = {"asaitems": asaitems}
        returned = _balance_totals_from_serialized_data(serialized_data)
        assert returned == {
            asset_id1: 1000.0,
            asset_id2: 0.0,
            asset_id3: 500.0,
            asset_id4: 0.0,
        }

    # # _base_chart_data_from_serialized_data
    def test_utils_charts_base_data_from_serialized_returns_empty_dict_for_empty_items(
        self,
    ):
        assert _base_chart_data_from_serialized_data([], {}) == {}

    def test_utils_charts_base_data_from_serialized_returns_empty_dict_for_zero_sum(
        self,
    ):
        # All rows with value=0 are filtered out by val_check; result is empty.
        asaitems = [_asaitem(0, 1, "A"), _asaitem(0, 2, "B")]
        assert _base_chart_data_from_serialized_data(asaitems, {}) == {}

    def test_utils_charts_base_data_from_serialized_returns_empty_dict_for_zero_sum2(
        self,
    ):
        # With val_check=False rows aren't filtered but sum is still 0.
        asaitems = [_asaitem(0, 1, "A"), _asaitem(0, 2, "B")]
        assert (
            _base_chart_data_from_serialized_data(asaitems, {}, val_check=False) == {}
        )

    def test_utils_charts_base_data_from_serialized_returns_same_size_lists(self):
        asaitems = [
            _asaitem(100, 1, "AAA"),
            _asaitem(50, 2, "BBB"),
            _asaitem(25, 3, "CCC"),
        ]
        returned = _base_chart_data_from_serialized_data(asaitems, {})
        assert (
            len(returned["labels"])
            == len(returned["data"])
            == len(returned["colors"])
            == 3
        )

    def test_utils_charts_base_data_from_serialized_skips_zero_valued_rows_when_val(
        self,
    ):
        asaitems = [
            _asaitem(100, 1, "AAA"),
            _asaitem(0, 2, "BBB"),
            _asaitem(25, 3, "CCC"),
        ]
        returned = _base_chart_data_from_serialized_data(asaitems, {})
        assert returned["labels"] == ["AAA", "CCC"]

    def test_utils_charts_base_data_from_serialized_includes_zero_valued_rows_not_val(
        self,
    ):
        # Used for NFT charts which need every collection shown regardless of value.
        asaitems = [
            _nftcollection(100, "CollA"),
            _nftcollection(0, "CollB"),
        ]
        returned = _base_chart_data_from_serialized_data(asaitems, {}, val_check=False)
        assert returned["labels"] == ["CollA", "CollB"]
        # Second row contributes 0% but the slot is present.
        assert returned["data"] == ["100.00000000", "0.00000000"]

    def test_utils_charts_base_data_from_serialized_calculates_percentages(self):
        # 800 / (800+150+50) = 80%, 150/1000 = 15%, 50/1000 = 5%
        asaitems = [
            _asaitem(800, 1, "AAA"),
            _asaitem(150, 2, "BBB"),
            _asaitem(50, 3, "CCC"),
        ]
        returned = _base_chart_data_from_serialized_data(asaitems, {})
        assert returned["data"] == [
            "80.00000000",
            "15.00000000",
            "5.00000000",
        ]

    def test_utils_charts_base_data_from_serialized_assigns_colors_from_distinct_color(
        self,
    ):
        asaitems = [_asaitem(100, 1, "AAA"), _asaitem(50, 2, "BBB")]
        returned = _base_chart_data_from_serialized_data(asaitems, {})
        assert returned["colors"] == [DISTINCT_COLORS[0], DISTINCT_COLORS[1]]

    def test_utils_charts_base_data_from_serialized_honors_distinct_colors_argument(
        self,
    ):
        # The NFT chart passes DISTINCT_COLORS_2 to differentiate from the ASA chart.
        asaitems = [_nftcollection(100, "X"), _nftcollection(50, "Y")]
        returned = _base_chart_data_from_serialized_data(
            asaitems, {}, distinct_colors=DISTINCT_COLORS_2, val_check=False
        )
        assert returned["colors"] == [DISTINCT_COLORS_2[0], DISTINCT_COLORS_2[1]]

    def test_utils_charts_base_data_from_serialized_updates_asa_colors_by_asset_id(
        self,
    ):
        asa_colors = {0: "algo"}
        asaitems = [
            _asaitem(100, 31566704, "USDC"),
            _asaitem(50, 226701642, "YLDY"),
        ]
        _base_chart_data_from_serialized_data(asaitems, asa_colors)
        # Note: the legacy _base_chart_data overwrites color slots by positional
        # index, so an ALGO row appearing at index 1 ends up keyed as "1" even
        # though the dict was pre-seeded with {0: "algo"}. This helper must
        # preserve that exact behavior for byte-compatible chart output.
        assert asa_colors == {0: "algo", 31566704: "0", 226701642: "1"}

    def test_utils_charts_base_data_from_serialized_updates_nft_colors_by_collection(
        self,
    ):
        # Collections lack an "asset" key, so we key on "name" instead.
        nft_colors = {}
        nftcollections = [
            _nftcollection(100, "AlgoSkull"),
            _nftcollection(50, "Pixel Punks"),
        ]
        _base_chart_data_from_serialized_data(
            nftcollections, nft_colors, val_check=False
        )
        assert nft_colors == {"AlgoSkull": "0", "Pixel Punks": "1"}

    def test_utils_charts_base_data_from_serialized_collapses_tail_into_others_bucket(
        self,
    ):
        # Top item is ~96%; the remaining tail should collapse into "others".
        asaitems = [
            _asaitem(960, 1, "AAA"),
            _asaitem(20, 2, "BBB"),
            _asaitem(10, 3, "CCC"),
            _asaitem(10, 4, "DDD"),
        ]
        with mock.patch("utils.charts.HIDE_LAST_PERCENT", 0.05):
            returned = _base_chart_data_from_serialized_data(asaitems, {})
        assert returned["labels"][-1] == "others"
        assert returned["colors"][-1] == ASASTATS_COLOR_OTHERS
        # "others" bucket carries the remaining 4%.
        assert returned["data"] == ["96.00000000", "4.00000000"]

    def test_utils_charts_base_data_from_serialized_does_not_collapse_when_last_hidden(
        self,
    ):
        # Legacy behavior: don't bother creating an "others" bucket holding a
        # single item; just keep the item as its own slot.
        asaitems = [
            _asaitem(980, 1, "AAA"),
            _asaitem(15, 2, "BBB"),
            _asaitem(5, 3, "CCC"),
        ]
        with mock.patch("utils.charts.HIDE_LAST_PERCENT", 0.005):
            returned = _base_chart_data_from_serialized_data(asaitems, {})
        assert "others" not in returned["labels"]
        assert len(returned["labels"]) == 3

    # # _consolidated_data_from_assets_data
    def test_utils_charts_consolidated_data_from_assets_data_functionality(
        self, mocker
    ):
        assets_data = mocker.MagicMock()
        mocked_balance = mocker.patch("utils.charts._balance_totals_from_assets_data")
        mocked_staked = mocker.patch("utils.charts._staked_totals_from_assets_data")
        mocked_liquidity = mocker.patch(
            "utils.charts._liquidity_totals_from_assets_data"
        )
        mocked_defi = mocker.patch("utils.charts._defi_totals_from_assets_data")
        returned = _consolidated_data_from_assets_data(assets_data)
        assert returned == Consolidated(
            mocked_balance.return_value,
            mocked_staked.return_value,
            mocked_liquidity.return_value,
            mocked_defi.return_value,
            (),
        )
        mocked_staked.assert_called_once_with(assets_data)
        mocked_liquidity.assert_called_once_with(assets_data)
        mocked_defi.assert_called_once_with(assets_data)

    # # _consolidated_data_from_serialized_data
    def test_utils_charts_consolidated_data_from_serialized_data_functionality(
        self, mocker
    ):
        serialized_data = mocker.MagicMock()
        mocked_balance = mocker.patch(
            "utils.charts._balance_totals_from_serialized_data"
        )
        mocked_staked = mocker.patch("utils.charts._staked_totals_from_serialized_data")
        mocked_liquidity = mocker.patch(
            "utils.charts._liquidity_totals_from_serialized_data"
        )
        mocked_defi = mocker.patch("utils.charts._defi_totals_from_serialized_data")
        mocked_nftfloor = mocker.patch(
            "utils.charts._nftfloor_totals_from_serialized_data"
        )
        returned = _consolidated_data_from_serialized_data(serialized_data)
        assert returned == Consolidated(
            mocked_balance.return_value,
            mocked_staked.return_value,
            mocked_liquidity.return_value,
            mocked_defi.return_value,
            mocked_nftfloor.return_value,
        )
        mocked_balance.assert_called_once_with(serialized_data)
        mocked_staked.assert_called_once_with(serialized_data)
        mocked_liquidity.assert_called_once_with(serialized_data)
        mocked_defi.assert_called_once_with(serialized_data)
        mocked_nftfloor.assert_called_once_with(serialized_data)

    # # _consolidated_totals_from_consolidated_data
    def test_utils_charts_consolidated_totals_from_consolidated_data_functionality(
        self,
    ):
        balance_values = {"1": 100, "2": 200, "3": 500}
        staked_values = {"1": 101, "2": 201, "3": 501}
        liquidity_values = {"1": 110, "2": 210, "3": 510}
        defi_values = {"1": 200, "2": 300, "3": 400}
        nftfloor_values = [[1000, 0, 1, 2, 3], [2000, 0, 1, 2, 3], [5000, 0, 1, 2, 3]]
        consolidated_data = Consolidated(
            balance_values,
            staked_values,
            liquidity_values,
            defi_values,
            nftfloor_values,
        )
        returned = _consolidated_totals_from_consolidated_data(consolidated_data)
        assert returned == Consolidated(800, 803, 830, 900, 8000)

    # # _defi_totals_from_assets_data
    def test_utils_charts_defi_totals_from_assets_data_functionality(self, mocker):
        asset_id1, asset_id2, asset_id3, asset_id4 = 505, 506, 507, 508
        elem1 = self._mocked_elem("Staked", "Some farm", 800, mocker)
        elem2 = self._mocked_elem("Balance", "name2", 700, mocker)
        elem3 = self._mocked_elem("Staked", "name3", 600, mocker)
        elem4 = self._mocked_elem("Deposit", "name4", 500, mocker)
        elem5 = self._mocked_elem("Staked", "Liquidity", 400, mocker)
        elem6 = self._mocked_elem("Staked", "Liquidity", 1800, mocker)
        elem7 = self._mocked_elem(None, "name7", 1900, mocker)
        elem8 = self._mocked_elem("Balance", "name8", 2000, mocker)
        elem9 = self._mocked_elem("Staked", "Cometa farming", 2100, mocker)
        elem10 = self._mocked_elem("Added", "Staked", 2200, mocker)
        elem11 = self._mocked_elem("Staked", "Humble farm", 2300, mocker)
        elem12 = self._mocked_elem("Staked", "Liquidity", 500, mocker)
        body1 = [elem1, elem2, elem3, elem4, elem5]
        body2 = [elem6, elem7, elem8, elem9, elem10, elem11]
        body3 = [elem12]
        body4 = []
        info1, info2, info3, info4 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        info1.id = asset_id1
        info2.id = asset_id2
        info3.id = asset_id3
        info4.id = asset_id4
        assets_data = {
            "asa": [
                {"info": info1, "body": body1},
                {"info": info2, "body": body2},
                {"info": info3, "body": body3},
                {"info": info4, "body": body4},
            ]
        }
        returned = _defi_totals_from_assets_data(assets_data)
        assert returned == {
            asset_id1: 1300.0,
            asset_id2: 8500.0,
            asset_id3: 0.0,
            asset_id4: 0.0,
        }

    # # _defi_totals_from_serialized_data
    def test_utils_charts_defi_totals_from_serialized_data_functionality(self):
        asset_id1, asset_id2, asset_id3, asset_id4 = 505, 506, 507, 508
        asaitems = [
            {
                "asset": {"id": asset_id1},
                "programs": [
                    {"program": {"name": "Some farm", "type": "Staked"}, "value": 800},
                    {"program": {"name": "program2", "type": "Balance"}, "value": 1000},
                    {"program": {"name": "program1", "type": "Staked"}, "value": 700},
                    {"program": {"name": "program8", "type": "Deposit"}, "value": 2000},
                ],
            },
            {
                "asset": {"id": asset_id2},
                "programs": [
                    {"program": {"name": "Liquidity", "type": "Added"}, "value": 100},
                    {"program": {"name": "program3"}, "value": 200},
                    {"program": {"name": "program2", "type": "Balance"}, "value": 700},
                    {"program": {"name": "Deposit", "type": "Added"}, "value": 400},
                ],
            },
            {
                "asset": {"id": asset_id3},
                "programs": [
                    {"program": {"name": "Liquidity", "type": "Staked"}, "value": 500},
                    {"program": {"name": "program5"}},
                ],
            },
            {"asset": {"id": asset_id4}},
        ]
        serialized_data = {"asaitems": asaitems}
        returned = _defi_totals_from_serialized_data(serialized_data)
        assert returned == {
            asset_id1: 2800.0,
            asset_id2: 600.0,
            asset_id3: 0.0,
            asset_id4: 0.0,
        }

    # # _distribution_chart_data_from_serialized_data
    def test_utils_charts_distribution_chart_data_from_serialized_data_empty_asaitems(
        self,
    ):
        consolidated = Consolidated({}, {}, {}, {}, ())
        assert (
            _distribution_chart_data_from_serialized_data(
                {"asaitems": []}, consolidated
            )
            == {}
        )

    def test_utils_charts_distribution_chart_data_from_serialized_data_for_zero_sum(
        self,
    ):
        asaitems = [_asaitem(0, 1, "A"), _asaitem(0, 2, "B")]
        consolidated = Consolidated({}, {}, {}, {}, ())
        assert (
            _distribution_chart_data_from_serialized_data(
                {"asaitems": asaitems}, consolidated
            )
            == {}
        )

    def test_utils_charts_distribution_chart_data_from_serialized_data_same_size_lists(
        self,
    ):
        asaitems = [
            _asaitem(100, 10, "A"),
            _asaitem(60, 20, "B"),
            _asaitem(40, 30, "C"),
        ]
        consolidated = Consolidated(
            balance={10: 50, 20: 30, 30: 20},
            staked={10: 25, 20: 15, 30: 10},
            liquidity={10: 15, 20: 10, 30: 5},
            defi={10: 10, 20: 5, 30: 5},
            nftfloor=(),
        )
        returned = _distribution_chart_data_from_serialized_data(
            {"asaitems": asaitems}, consolidated
        )
        assert returned["labels"] == ["A", "B", "C"]
        for segment_name in DISTRIBUTION_COLORS:
            assert len(returned["data"][segment_name.lower()]) == 3

    def test_utils_charts_distribution_chart_data_from_serialized_data_per_segment(
        self,
    ):
        asaitems = [
            _asaitem(100, 10, "A"),
            _asaitem(60, 20, "B"),
        ]
        consolidated = Consolidated(
            balance={10: 70, 20: 40},
            staked={10: 20, 20: 15},
            liquidity={10: 10, 20: 5},
            defi={10: 0, 20: 0},
            nftfloor=(),
        )
        returned = _distribution_chart_data_from_serialized_data(
            {"asaitems": asaitems}, consolidated
        )
        # _distribution_chart_data emits per-segment values (not percentages),
        # so we can sanity-check the lookup logic directly.
        assert returned["data"]["balance"] == ["70.00000000", "40.00000000"]
        assert returned["data"]["staked"] == ["20.00000000", "15.00000000"]

    def test_utils_charts_distribution_chart_data_from_serialized_data_collapses_tail(
        self,
    ):
        asaitems = [
            _asaitem(960, 10, "A"),
            _asaitem(20, 20, "B"),
            _asaitem(10, 30, "C"),
            _asaitem(10, 40, "D"),
        ]
        consolidated = Consolidated(
            balance={10: 500, 20: 10, 30: 5, 40: 5},
            staked={10: 300, 20: 5, 30: 3, 40: 2},
            liquidity={10: 100, 20: 3, 30: 1, 40: 1},
            defi={10: 60, 20: 2, 30: 1, 40: 2},
            nftfloor=(),
        )
        with mock.patch("utils.charts.HIDE_LAST_PERCENT", 0.05):
            returned = _distribution_chart_data_from_serialized_data(
                {"asaitems": asaitems}, consolidated
            )
        assert returned["labels"] == ["A", "others"]
        # "others" carries the segment-summed tail: 10+5+5 for balance, etc.
        assert returned["data"]["balance"] == ["500.00000000", "20.00000000"]
        assert returned["data"]["staked"] == ["300.00000000", "10.00000000"]
        assert returned["data"]["liquidity"] == ["100.00000000", "5.00000000"]
        assert returned["data"]["defi"] == ["60.00000000", "5.00000000"]

    # # _distribution_chart_from_serialized_data
    def test_utils_charts_distribution_chart_from_serialized_data_functionality(
        self, mocker
    ):
        mocked_setup = mocker.patch("utils.charts._distribution_setup")
        mocked_data = mocker.patch(
            "utils.charts._distribution_chart_data_from_serialized_data",
            return_value={"labels": ["X"], "data": {"balance": ["100.0"]}},
        )
        serialized_data = mocker.MagicMock()
        consolidated_data = mocker.MagicMock()
        returned = _distribution_chart_from_serialized_data(
            serialized_data, consolidated_data
        )
        assert returned == mocked_setup.return_value
        mocked_data.assert_called_once_with(serialized_data, consolidated_data)
        mocked_setup.assert_called_once_with(labels=["X"], data={"balance": ["100.0"]})

    # # _liquidity_totals_from_assets_data
    def test_utils_charts_liquidity_totals_from_assets_data_functionality(self, mocker):
        asset_id1, asset_id2, asset_id3, asset_id4 = 505, 506, 507, 508
        elem1 = self._mocked_elem("Staked", "Some farm", 800, mocker, source="Some LP")
        elem2 = self._mocked_elem("Balance", "name2", 700, mocker)
        elem3 = self._mocked_elem("Staked", "name3", 600, mocker)
        elem4 = self._mocked_elem("Deposit", "name4", 500, mocker)
        elem5 = self._mocked_elem("Staked", "Liquidity", 400, mocker, source="Pact LP")
        elem6 = self._mocked_elem("Staked", "Liquidity", 1800, mocker)
        elem7 = self._mocked_elem(None, "name7", 1900, mocker)
        elem8 = self._mocked_elem("Balance", "name8", 2000, mocker)
        elem9 = self._mocked_elem(
            "Staked", "Cometa farming", 2100, mocker, source="Tinyman LP"
        )
        elem10 = self._mocked_elem("Added", "Staked", 2200, mocker)
        elem11 = self._mocked_elem("Staked", "Humble farm", 2300, mocker)
        elem12 = self._mocked_elem("Staked", "Liquidity", 500, mocker, source="LP")
        body1 = [elem1, elem2, elem3, elem4, elem5]
        body2 = [elem6, elem7, elem8, elem9, elem10, elem11]
        body3 = [elem12]
        body4 = []
        info1, info2, info3, info4 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        info1.id = asset_id1
        info2.id = asset_id2
        info3.id = asset_id3
        info4.id = asset_id4
        assets_data = {
            "asa": [
                {"info": info1, "body": body1},
                {"info": info2, "body": body2},
                {"info": info3, "body": body3},
                {"info": info4, "body": body4},
            ]
        }
        returned = _liquidity_totals_from_assets_data(assets_data)
        assert returned == {
            asset_id1: 1200.0,
            asset_id2: 2100.0,
            asset_id3: 500.0,
            asset_id4: 0.0,
        }

    # # _liquidity_totals_from_serialized_data
    def test_utils_charts_liquidity_totals_from_serialized_data_functionality(self):
        asset_id1, asset_id2, asset_id3, asset_id4 = 505, 506, 507, 508
        asaitems = [
            {
                "asset": {"id": asset_id1},
                "programs": [
                    {"program": {"name": "Some farm", "type": "Staked"}, "value": 800},
                    {"program": {"name": "program2", "type": "Balance"}, "value": 1000},
                    {"program": {"name": "program1", "type": "Staked"}, "value": 700},
                    {"program": {"name": "program8", "type": "Deposit"}, "value": 2000},
                    {"program": {"name": "Liquidity", "type": "Added"}, "value": 1000},
                ],
            },
            {
                "asset": {"id": asset_id2},
                "programs": [
                    {"program": {"name": "Liquidity", "type": "Added"}, "value": 100},
                    {"program": {"name": "program3"}, "value": 200},
                    {"program": {"name": "program2", "type": "Balance"}, "value": 700},
                    {"program": {"name": "Deposit", "type": "Added"}, "value": 400},
                    {"program": {"name": "Liquidity", "type": "Added"}, "value": 700},
                    {"program": {"name": "Liquid", "type": "Added"}, "value": 700},
                ],
            },
            {
                "asset": {"id": asset_id3},
                "programs": [
                    {"program": {"name": "Liquidity", "type": "Staked"}, "value": 500},
                    {"program": {"name": "program5"}},
                ],
            },
            {"asset": {"id": asset_id4}},
        ]
        serialized_data = {"asaitems": asaitems}
        returned = _liquidity_totals_from_serialized_data(serialized_data)
        assert returned == {
            asset_id1: 1000.0,
            asset_id2: 800.0,
            asset_id3: 0.0,
            asset_id4: 0.0,
        }

    # # _nft_chart_from_serialized_data
    def test_utils_charts_nft_chart_from_serialized_data_functionality(self, mocker):
        nft_colors = mocker.MagicMock()
        chart_data = {"labels": ["x"], "data": ["y"], "colors": ["z"]}
        mocked_base = mocker.patch(
            "utils.charts._base_chart_data_from_serialized_data",
            return_value=chart_data,
        )
        mocked_setup = mocker.patch("utils.charts._chart_setup")
        returned = _nft_chart_from_serialized_data(
            {"nftcollections": ["c"]}, nft_colors
        )
        assert returned == mocked_setup.return_value
        mocked_base.assert_called_once_with(
            ["c"], nft_colors, distinct_colors=DISTINCT_COLORS_2, val_check=False
        )
        mocked_setup.assert_called_once_with(
            "NFT data", labels=["x"], data=["y"], colors=["z"]
        )

    def test_utils_charts_nft_chart_from_serialized_data_for_missing_collections(
        self, mocker
    ):
        mocked_base = mocker.patch(
            "utils.charts._base_chart_data_from_serialized_data", return_value={}
        )
        mocked_setup = mocker.patch("utils.charts._chart_setup")
        _nft_chart_from_serialized_data({}, mocker.MagicMock(), label="custom")
        mocked_base.assert_called_once_with(
            [], mocker.ANY, distinct_colors=DISTINCT_COLORS_2, val_check=False
        )
        mocked_setup.assert_called_once_with("custom")

    # # _nftfloor_totals_from_serialized_data
    def test_utils_charts_nftfloor_totals_from_serialized_data_functionality(self):
        collection1, collection2, collection3, collection4 = (
            "collection1",
            "collection2",
            "collection3",
            "collection4",
        )
        nftcollections = [
            {
                "name": collection1,
                "nfts": [
                    {"nft": {"floor": [{"price": "2.50000"}]}, "amount": 1},
                    {"nft": {"floor": [{"price": "10.0000"}]}, "amount": 2},
                    {"nft": {"floor": [{"price": "22.50000"}]}},
                    {"nft": {"floor": []}, "amount": 1},
                    {"nft": {}, "amount": 2},
                    {"nft": {"floor": [{"price": "40.0500"}]}, "amount": 1},
                ],
            },
            {
                "name": collection2,
                "nfts": [
                    {"nft": {"floor": [{"price": "100.50000"}]}},
                    {"nft": {}, "amount": 2},
                    {"nft": {"floor": [{"foo": "500.0000"}]}, "amount": 1},
                ],
            },
            {
                "name": collection3,
                "nfts": [
                    {"nft": {"floor": [{"price": "700.0000"}]}, "amount": 1},
                    {"nft": {"floor": [{"price": "308.25600"}]}, "amount": 1},
                    {"nft": {"floor": [{"price": "2.50000"}]}},
                    {"nft": {"floor": [{"price": "2.50000"}]}, "amount": 1},
                ],
            },
            {"name": collection4},
            {
                "nfts": [
                    {"nft": {"floor": [{"price": "500.0000"}]}, "amount": 2},
                    {"nft": {"floor": [{"price": "4000.50000"}]}},
                    {"nft": {"floor": [{"price": "20000.25000"}]}, "amount": 1},
                ],
            },
        ]
        serialized_data = {"nftcollections": nftcollections}
        returned = _nftfloor_totals_from_serialized_data(serialized_data)
        assert returned == [
            (21000.25, ""),
            (1010.756, collection3),
            (62.55, collection1),
            (0.0, collection4),
            (0.0, collection2),
        ]

    # # _staked_totals_from_assets_data
    def test_utils_charts_staked_totals_from_assets_data_functionality(self, mocker):
        asset_id1, asset_id2, asset_id3, asset_id4 = 505, 506, 507, 508
        elem1 = self._mocked_elem("Staked", "Some farm", 800, mocker)
        elem2 = self._mocked_elem("Balance", "name2", 700, mocker)
        elem3 = self._mocked_elem("Staked", "name3", 600, mocker)
        elem4 = self._mocked_elem("Deposit", "name4", 500, mocker)
        elem5 = self._mocked_elem("Staked", "Liquidity", 400, mocker)
        elem6 = self._mocked_elem("Staked", "Liquidity", 1800, mocker)
        elem7 = self._mocked_elem(None, "name7", 1900, mocker)
        elem8 = self._mocked_elem("Balance", "name8", 2000, mocker)
        elem9 = self._mocked_elem("Staked", "Cometa farming", 2100, mocker)
        elem10 = self._mocked_elem("Added", "Staked", 2200, mocker)
        elem11 = self._mocked_elem("Staked", "Humble farm", 2300, mocker)
        elem12 = self._mocked_elem("Staked", "Liquidity", 500, mocker)
        body1 = [elem1, elem2, elem3, elem4, elem5]
        body2 = [elem6, elem7, elem8, elem9, elem10, elem11]
        body3 = [elem12]
        body4 = []
        info1, info2, info3, info4 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        info1.id = asset_id1
        info2.id = asset_id2
        info3.id = asset_id3
        info4.id = asset_id4
        assets_data = {
            "asa": [
                {"info": info1, "body": body1},
                {"info": info2, "body": body2},
                {"info": info3, "body": body3},
                {"info": info4, "body": body4},
            ]
        }
        returned = _staked_totals_from_assets_data(assets_data)
        assert returned == {
            asset_id1: 1000.0,
            asset_id2: 1800.0,
            asset_id3: 500.0,
            asset_id4: 0.0,
        }

    # # _staked_totals_from_serialized_data
    def test_utils_charts_staked_totals_from_serialized_data_functionality(self):
        asset_id1, asset_id2, asset_id3, asset_id4 = 505, 506, 507, 508
        asaitems = [
            {
                "asset": {"id": asset_id1},
                "programs": [
                    {"program": {"name": "Some farm", "type": "Staked"}, "value": 800},
                    {"program": {"name": "program2", "type": "Balance"}, "value": 1000},
                    {"program": {"name": "program1", "type": "Staked"}, "value": 700},
                    {"program": {"name": "program8", "type": "Deposit"}, "value": 2000},
                    {"program": {"name": "Liquidity", "type": "Staked"}, "value": 1000},
                ],
            },
            {
                "asset": {"id": asset_id2},
                "programs": [
                    {"program": {"name": "Liquidity", "type": "Staked"}, "value": 100},
                    {"program": {"name": "program3"}, "value": 200},
                    {"program": {"name": "program2", "type": "Balance"}, "value": 700},
                    {
                        "program": {"name": "Cometa farming", "type": "Staked"},
                        "value": 400,
                    },
                    {"program": {"name": "Staked", "type": "Added"}, "value": 700},
                    {
                        "program": {"name": "Humble farm", "type": "Staked"},
                        "value": 700,
                    },
                ],
            },
            {
                "asset": {"id": asset_id3},
                "programs": [
                    {"program": {"name": "Liquidity", "type": "Staked"}, "value": 500},
                    {"program": {"name": "program5"}},
                ],
            },
            {"asset": {"id": asset_id4}},
        ]
        serialized_data = {"asaitems": asaitems}
        returned = _staked_totals_from_serialized_data(serialized_data)
        assert returned == {
            asset_id1: 1700.0,
            asset_id2: 100.0,
            asset_id3: 500.0,
            asset_id4: 0.0,
        }

    # # _total_from_serialized_data
    def test_utils_charts_total_from_serialized_data_casts_decimal_strings_to_floats(
        self,
    ):
        serialized_data = {
            "total": {
                "algo": "169.514449",
                "asa": "217.002659",
                "nft": "1494.992484",
                "total": "1881.509592",
                "totalusdc": "216.302465",
                "priceusdc": "8.698512",
                "pricealgo": "0.114962",
                "noteval": 1,
            }
        }
        total = _total_from_serialized_data(serialized_data)
        assert isinstance(total, Total)
        assert total.algo == pytest.approx(169.514449)
        assert total.asa == pytest.approx(217.002659)
        assert total.nft == pytest.approx(1494.992484)
        assert total.total == pytest.approx(1881.509592)
        assert total.totalusdc == pytest.approx(216.302465)
        assert total.priceusdc == pytest.approx(8.698512)
        assert total.pricealgo == pytest.approx(0.114962)
        assert total.noteval == 1

    def test_utils_charts_total_from_serialized_data_handles_missing_total_key(self):
        # An API response with no spendable account still has to render zeroed
        # totals; chart code downstream divides by total.total and must not crash.
        total = _total_from_serialized_data({})
        assert total == Total(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)

    def test_utils_charts_total_from_serialized_data_handles_null_total_value(self):
        # serializer may emit explicit nulls for empty accounts.
        total = _total_from_serialized_data({"total": None})
        assert total == Total(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)

    def test_utils_charts_total_from_serialized_data_handles_garbage_values_without_crashing(
        self,
    ):
        # If the upstream cache somehow contains malformed data, fall back to 0
        # rather than raising. This protects the website from a single bad row
        # taking down the entire address page.
        total = _total_from_serialized_data(
            {"total": {"algo": "not-a-number", "total": "5.0"}}
        )
        assert total.algo == 0.0
        assert total.total == pytest.approx(5.0)

    def test_utils_charts_total_from_serialized_data_ignores_unknown_extra_fields(self):
        # The API 2.0 Total carries totalwonft / totalwonftusdc fields that
        # utils.structs.Total doesn't declare; they must be silently ignored.
        serialized_data = {
            "total": {
                "algo": "1.0",
                "asa": "0.0",
                "nft": "0.0",
                "total": "1.0",
                "totalusdc": "0.5",
                "priceusdc": "0.5",
                "pricealgo": "1.0",
                "noteval": 0,
                "totalwonft": "1.0",
                "totalwonftusdc": "0.5",
            }
        }
        total = _total_from_serialized_data(serialized_data)
        assert total.total == pytest.approx(1.0)

    # # _unit_for_asaitem
    def test_utils_charts_unit_for_asaitem_returns_unit_when_present(self):
        asaitem = {"asset": {"id": 31566704, "unit": "USDC"}}
        assert _unit_for_asaitem(asaitem) == "USDC"

    def test_utils_charts_unit_for_asaitem_utils_charts_unit_for_asaitem_returns_id(
        self,
    ):
        asaitem = {"asset": {"id": 31566704, "unit": ""}}
        assert _unit_for_asaitem(asaitem) == 31566704

    def test_utils_charts_unit_for_asaitem_utils_charts_unit_for_asaitem_returns_algo(
        self,
    ):
        assert _unit_for_asaitem({}) == "ALGO"

    def test_utils_charts_unit_for_asaitem_utils_charts_unit_for_asaitem_asset_is_none(
        self,
    ):
        # An incomplete payload shouldn't crash chart preparation.
        assert _unit_for_asaitem({"asset": None}) == "ALGO"


class TestUtilsChartConsolidatedPublicFunctions:

    # # prepare_consolidated_charts
    def test_utils_charts_prepare_consolidated_charts_functionality(self, mocker):
        serialized_data, asas, values, total, nft_colors = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        consolidated_data = mocker.MagicMock()
        mocked_data = mocker.patch(
            "utils.charts._consolidated_data_from_serialized_data",
            return_value=consolidated_data,
        )
        consolidated_totals = mocker.MagicMock()
        mocked_totals = mocker.patch(
            "utils.charts._consolidated_totals_from_consolidated_data",
            return_value=consolidated_totals,
        )
        mocked_dist = mocker.patch("utils.charts._distribution_chart")
        mocked_ratio = mocker.patch("utils.charts._ratio_chart")
        mocked_nftfloor = mocker.patch("utils.charts._nft_chart")
        mocked_assign = mocker.patch("utils.charts._assign_nftfloor_colors")
        returned = prepare_consolidated_charts(
            serialized_data, asas, values, total, nft_colors
        )
        assert returned == (
            mocked_dist.return_value,
            mocked_ratio.return_value,
            mocked_nftfloor.return_value,
            consolidated_totals,
        )
        mocked_data.asset_called_once()
        mocked_data.asset_called_with(serialized_data)
        mocked_totals.asset_called_once()
        mocked_totals.asset_called_with(consolidated_data)
        mocked_dist.assert_called_once_with(asas, values, consolidated_data)
        mocked_ratio.assert_called_once_with(total, consolidated_totals)
        mocked_nftfloor.assert_called_once_with(
            consolidated_data.nftfloor, {}, label="NFT floor data"
        )
        mocked_assign.assert_called_once_with(mocked_nftfloor.return_value, nft_colors)

    # # prepare_consolidated_charts_from_assets_data
    def test_utils_charts_prepare_consolidated_charts_from_assets_data_functionality(
        self, mocker
    ):
        total = mocker.MagicMock()
        assets_data = {"total": total}
        consolidated_data = mocker.MagicMock()
        mocked_data = mocker.patch(
            "utils.charts._consolidated_data_from_assets_data",
            return_value=consolidated_data,
        )
        consolidated_totals = mocker.MagicMock()
        mocked_totals = mocker.patch(
            "utils.charts._consolidated_totals_from_consolidated_data",
            return_value=consolidated_totals,
        )
        mocked_dist = mocker.patch("utils.charts._distribution_chart_from_assets_data")
        mocked_ratio = mocker.patch("utils.charts._ratio_chart")
        returned = prepare_consolidated_charts_from_assets_data(assets_data)
        assert returned == (
            mocked_dist.return_value,
            mocked_ratio.return_value,
            consolidated_totals,
        )
        mocked_data.assert_called_once_with(assets_data)
        mocked_totals.assert_called_once_with(consolidated_data)
        mocked_dist.assert_called_once_with(assets_data, consolidated_data)
        mocked_ratio.assert_called_once_with(total, consolidated_totals)

    # # prepare_consolidated_charts_from_serialized_data
    def test_utils_chart_prepare_consolidated_charts_from_serialized_data_functionality(
        self, mocker
    ):
        serialized_data = mocker.MagicMock()
        nft_colors = mocker.MagicMock()
        consolidated_data = mocker.MagicMock()
        consolidated_totals = mocker.MagicMock()
        total = mocker.MagicMock()
        mocked_data = mocker.patch(
            "utils.charts._consolidated_data_from_serialized_data",
            return_value=consolidated_data,
        )
        mocked_totals = mocker.patch(
            "utils.charts._consolidated_totals_from_consolidated_data",
            return_value=consolidated_totals,
        )
        mocked_total = mocker.patch(
            "utils.charts._total_from_serialized_data",
            return_value=total,
        )
        mocked_dist = mocker.patch(
            "utils.charts._distribution_chart_from_serialized_data"
        )
        mocked_ratio = mocker.patch("utils.charts._ratio_chart")
        mocked_nftfloor = mocker.patch("utils.charts._nft_chart")
        mocked_assign = mocker.patch("utils.charts._assign_nftfloor_colors")

        returned = prepare_consolidated_charts_from_serialized_data(
            serialized_data, nft_colors
        )

        assert returned == (
            mocked_dist.return_value,
            mocked_ratio.return_value,
            mocked_nftfloor.return_value,
            consolidated_totals,
        )
        mocked_data.assert_called_once_with(serialized_data)
        mocked_totals.assert_called_once_with(consolidated_data)
        mocked_total.assert_called_once_with(serialized_data)
        mocked_dist.assert_called_once_with(serialized_data, consolidated_data)
        mocked_ratio.assert_called_once_with(total, consolidated_totals)
        mocked_nftfloor.assert_called_once_with(
            consolidated_data.nftfloor, {}, label="NFT floor data"
        )
        mocked_assign.assert_called_once_with(mocked_nftfloor.return_value, nft_colors)
