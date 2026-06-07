"""Testing module for :py:mod:`utils.charts` module."""

import json
from collections import namedtuple
from copy import deepcopy
from pathlib import Path
from unittest import mock

import pytest

from utils.charts import (
    _asa_chart,
    _asa_chart_from_assets_data,
    _assign_nftfloor_colors,
    _base_chart_data,
    _base_chart_data_from_assets_data,
    _chart_setup,
    _distribution_chart,
    _distribution_chart_data,
    _distribution_chart_data_from_assets_data,
    _distribution_chart_from_assets_data,
    _distribution_setup,
    _nft_chart,
    _nft_chart_from_assets_data,
    _ratio_chart,
    _ratio_chart_data,
    _total_from_serialized_data,
    prepare_base_charts,
    prepare_base_charts_from_assets_data,
    prepare_base_charts_from_serialized_data,
    prepare_consolidated_charts_from_serialized_data,
)
from utils.constants.charts import (
    ASASTATS_COLOR_OTHERS,
    CHART_NFT_COLOR,
    DISTINCT_COLORS_2,
    DISTRIBUTION_COLORS,
)
from utils.structs import Consolidated, Total

from .fixtures import TESTING_ASAS, TESTING_ASAS_SMALL, TESTING_VALUES_SMALL

SAMPLE_PAYLOAD_PATH = Path(__file__).parent / "sample_serialized_540A5.json"


@pytest.fixture(scope="module")
def sample_payload():
    """Realistic API 2.0 serialized payload (76 asaitems, 55 NFT collections)."""
    with SAMPLE_PAYLOAD_PATH.open() as f:
        return json.load(f)


class TestUtilsChartFunctions:
    """Testing class for :py:mod:`utils.charts` functions."""

    # # _asa_chart
    def test_utils_charts_asa_chart_functionality(self, mocker):
        mocked_setup = mocker.patch("utils.charts._chart_setup")
        mocked_base = mocker.patch(
            "utils.charts._base_chart_data",
            return_value={"foo1": "bar1", "foo2": "bar2"},
        )
        asas, values, asa_colors = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        returned = _asa_chart(asas, values, asa_colors)
        assert returned == mocked_setup.return_value
        mocked_base.assert_called_once_with(asas, values, asa_colors)
        mocked_setup.assert_called_once_with("ASA data", foo1="bar1", foo2="bar2")

    # # _asa_chart_from_assets_data
    def test_utils_charts_asa_chart_from_assets_data_functionality(self, mocker):
        mocked_setup = mocker.patch("utils.charts._chart_setup")
        mocked_base = mocker.patch(
            "utils.charts._base_chart_data_from_assets_data",
            return_value={"foo1": "bar1", "foo2": "bar2"},
        )
        asa_data, asa_colors = (mocker.MagicMock(), mocker.MagicMock())
        returned = _asa_chart_from_assets_data(asa_data, asa_colors)
        assert returned == mocked_setup.return_value
        mocked_base.assert_called_once_with(asa_data, asa_colors)
        mocked_setup.assert_called_once_with("ASA data", foo1="bar1", foo2="bar2")

    # # _assign_nftfloor_colors
    def test_utils_charts_assign_nftfloor_colors(self):
        chart = {
            "labels": ["UNIT1", "UNIT2", "UNIT3", "UNIT4"],
            "datasets": [
                {
                    "label": "label",
                    "data": [],
                    "backgroundColor": [],
                    "borderWidth": 1,
                    "hoverOffset": 0,
                }
            ],
        }
        nft_colors = {"UNIT1": "1", "UNIT2": "3", "UNIT4": "9"}
        _assign_nftfloor_colors(chart, nft_colors)
        assert chart == {
            "labels": ["UNIT1", "UNIT2", "UNIT3", "UNIT4"],
            "datasets": [
                {
                    "label": "label",
                    "data": [],
                    "backgroundColor": [
                        DISTINCT_COLORS_2[1],
                        DISTINCT_COLORS_2[3],
                        ASASTATS_COLOR_OTHERS,
                        DISTINCT_COLORS_2[9],
                    ],
                    "borderWidth": 1,
                    "hoverOffset": 0,
                }
            ],
        }

    # # _base_chart_data
    def test_utils_charts_base_chart_data_returns_empty_dict_for_zero_sum(self, mocker):
        returned = _base_chart_data(
            mocker.MagicMock(), [[0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5]], {}
        )
        assert returned == {}

    def test_utils_charts_base_chart_data_returns_empty_dict_for_empty_values(
        self, mocker
    ):
        returned = _base_chart_data(mocker.MagicMock(), [], {})
        assert returned == {}

    def test_utils_charts_base_chart_data_returns_same_size_list(self):
        returned = _base_chart_data(TESTING_ASAS_SMALL, TESTING_VALUES_SMALL, {})
        assert isinstance(returned.get("labels"), (list,))
        assert isinstance(returned.get("data"), (list,))
        assert isinstance(returned.get("colors"), (list,))
        assert (
            len(returned.get("labels"))
            == len(returned.get("data"))
            == len(returned.get("colors"))
            == len(TESTING_VALUES_SMALL)
        )

    def test_utils_charts_base_chart_data_returns_limited_size(self):
        hide_last_percent = 0.04
        with mock.patch("utils.charts.HIDE_LAST_PERCENT", hide_last_percent):
            returned = _base_chart_data(TESTING_ASAS_SMALL, TESTING_VALUES_SMALL, {})
            assert (
                len(returned.get("labels"))
                == len(returned.get("data"))
                == len(returned.get("colors"))
                == 3
            )
            assert returned.get("labels")[-1] == "others"

    def test_utils_charts_base_chart_data_doesnt_reduce_size_when_last_item_left(self):
        hide_last_percent = 0.01
        with mock.patch("utils.charts.HIDE_LAST_PERCENT", hide_last_percent):
            returned = _base_chart_data(TESTING_ASAS_SMALL, TESTING_VALUES_SMALL, {})
            assert (
                len(returned.get("labels"))
                == len(returned.get("data"))
                == len(returned.get("colors"))
                == 4
            )
            assert returned.get("labels")[-1] != "others"

    def test_utils_charts_base_chart_data_calculates_totals(self):
        returned = _base_chart_data(TESTING_ASAS_SMALL, TESTING_VALUES_SMALL, {})
        assert returned.get("data") == [
            "95.58787766",
            "2.57206968",
            "0.94273163",
            "0.89732104",
        ]

    def test_utils_charts_base_chart_data_totals_for_values_with_negative_row(self):
        val_copy = deepcopy(TESTING_VALUES_SMALL)
        val_copy[2][0] = -100.0
        values = deepcopy(val_copy)
        returned = _base_chart_data(TESTING_ASAS_SMALL, values, {})
        assert returned.get("data") == ["96.49759097", "2.59654816", "0.90586087"]

    # # _base_chart_data_from_assets_data
    def test_utils_charts_base_chart_data_from_assets_data_returns_empty_dict_for_no_sum(
        self, mocker
    ):
        header1, header2, header3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        header1.total = 0
        header2.total = 0
        header3.total = 0
        asset_data = [{"header": header1}, {"header": header2}, {"header": header3}]
        returned = _base_chart_data_from_assets_data(asset_data, mocker.MagicMock())
        assert returned == {}

    def test_utils_charts_base_chart_data_from_assets_data_returns_same_size_list(
        self, mocker
    ):
        header1, header2, header3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        header1.total = 10
        header2.total = 20
        header3.total = 30
        asset_data = [{"header": header1}, {"header": header2}, {"header": header3}]
        returned = _base_chart_data_from_assets_data(asset_data, mocker.MagicMock())
        assert isinstance(returned.get("labels"), (list,))
        assert isinstance(returned.get("data"), (list,))
        assert isinstance(returned.get("colors"), (list,))
        assert (
            len(returned.get("labels"))
            == len(returned.get("data"))
            == len(returned.get("colors"))
            == 3
        )

    def test_utils_charts_base_chart_data_from_assets_data_doesnt_reduce_last_item_left(
        self, mocker
    ):
        header1, header2, header3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        header1.total = 10
        header1.label = "label1"
        header2.total = 20
        header2.label = "label2"
        header3.total = 30
        header3.label = "label3"
        asset_data = [{"header": header1}, {"header": header2}, {"header": header3}]
        hide_last_percent = 0.01
        with mock.patch("utils.charts.HIDE_LAST_PERCENT", hide_last_percent):
            returned = _base_chart_data_from_assets_data(asset_data, mocker.MagicMock())
            assert (
                len(returned.get("labels"))
                == len(returned.get("data"))
                == len(returned.get("colors"))
                == 3
            )
            assert returned.get("labels")[-1] != "others"

    def test_utils_charts_base_chart_data_from_assets_data_calculates_totals(
        self, mocker
    ):
        header1, header2, header3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        header1.total = 10
        header1.label = "label1"
        header2.total = 20
        header2.label = "label2"
        header3.total = 70
        header3.label = "label3"
        asset_data = [{"header": header1}, {"header": header2}, {"header": header3}]
        returned = _base_chart_data_from_assets_data(asset_data, mocker.MagicMock())
        assert returned.get("data") == ["10.00000000", "20.00000000", "70.00000000"]

    def test_utils_charts_base_chart_data_from_assets_data_updates_colors(self, mocker):
        header1, header2, header3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        header1.total = 10
        header1.label = "label1"
        header2.total = 20
        header2.label = "label2"
        header3.total = 70
        header3.label = "label3"
        asset_data = [{"header": header1}, {"header": header2}, {"header": header3}]
        asa_colors = {"label0": "5"}
        _base_chart_data_from_assets_data(asset_data, asa_colors)
        assert asa_colors == {
            "label0": "5",
            "label1": "0",
            "label2": "1",
            "label3": "2",
        }

    def test_utils_charts_base_chart_data_from_assets_data_appends_others(self, mocker):
        header1, header2, header3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        header1.total, header2.total, header3.total = 100000, 1, 1
        header1.label, header2.label, header3.label = "A", "B", "C"
        asset_data = [{"header": header1}, {"header": header2}, {"header": header3}]
        returned = _base_chart_data_from_assets_data(asset_data, mocker.MagicMock())
        assert returned["labels"] == ["A", "others"]
        assert len(returned["data"]) == 2
        assert len(returned["colors"]) == 2

    # # _chart_setup
    def test_utils_charts_chart_setup_returns_with_provided_label(self):
        label = "label"
        returned = _chart_setup(label)
        assert returned.get("datasets")[0].get("label") == label

    def test_utils_charts_chart_setup_returns_empty_list_for_labels_not_provided(self):
        returned = _chart_setup("foo")
        assert returned.get("labels") == []

    def test_utils_charts_chart_setup_returns_empty_list_for_data_not_provided(self):
        returned = _chart_setup("foo")
        assert returned.get("datasets")[0].get("data") == []

    def test_utils_charts_chart_setup_returns_empty_list_for_colors_not_provided(self):
        returned = _chart_setup("foo")
        assert returned.get("datasets")[0].get("backgroundColor") == []

    def test_utils_charts_chart_setup_functionality(self):
        returned = _chart_setup(
            "main label",
            labels=["ALGO", "USDC", "ASASTATS"],
            data=["20.5", "50.4", "29.1"],
            colors=["color1", "color2", "color3"],
        )
        assert returned == {
            "labels": ["ALGO", "USDC", "ASASTATS"],
            "datasets": [
                {
                    "label": "main label",
                    "data": ["20.5", "50.4", "29.1"],
                    "backgroundColor": ["color1", "color2", "color3"],
                    "borderWidth": 1,
                    "hoverOffset": 0,
                }
            ],
        }

    # # _base_chart_data
    def test_utils_charts_base_chart_data_returns_labels(self):
        returned = _base_chart_data({}, [[1, 2, 3, {}, 5]], {0: "algo"})
        assert returned.get("labels") == [2]

    def test_utils_charts_base_chart_data_returns_data(self):
        returned = _base_chart_data({}, [[1, 2, 3, {}, 5]], {0: "algo"})
        assert returned.get("data") == ["100.00000000"]

    def test_utils_charts_base_chart_data_returns_colors(self):
        returned = _base_chart_data({}, [[1, 2, 3, {}, 5]], {0: "algo"})
        assert returned.get("colors") == ["#e6194B"]

    # # _distribution_chart
    def test_utils_charts_distribution_chart_functionality(self, mocker):
        mocked_setup = mocker.patch("utils.charts._distribution_setup")
        mocked_distribution = mocker.patch(
            "utils.charts._distribution_chart_data", return_value={"a": "b"}
        )
        asas, values, consolidated_data = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        returned = _distribution_chart(asas, values, consolidated_data)
        assert returned == mocked_setup.return_value
        mocked_distribution.assert_called_once_with(asas, values, consolidated_data)
        mocked_setup.assert_called_once_with(a="b")

    # # _distribution_chart_data
    def test_utils_charts_distribution_chart_data_returns_empty_dict_for_zero_sum(
        self, mocker
    ):
        returned = _distribution_chart_data(
            mocker.MagicMock(), [[0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5]], {}
        )
        assert returned == {}

    def test_utils_charts_distribution_chart_data_returns_same_size_list(self):
        consolidated_data = Consolidated(
            {row[1]: (i + 1) * 1 for i, row in enumerate(TESTING_VALUES_SMALL)},
            {row[1]: (i + 1) * 10 for i, row in enumerate(TESTING_VALUES_SMALL)},
            {row[1]: (i + 1) * 100 for i, row in enumerate(TESTING_VALUES_SMALL)},
            {row[1]: (i + 1) * 1000 for i, row in enumerate(TESTING_VALUES_SMALL)},
            {row[1]: (i + 1) * 10000 for i, row in enumerate(TESTING_VALUES_SMALL)},
        )
        returned = _distribution_chart_data(
            TESTING_ASAS_SMALL, TESTING_VALUES_SMALL, consolidated_data
        )
        assert isinstance(returned.get("labels"), list)
        assert isinstance(returned.get("data"), dict)
        assert len(returned.get("labels")) == len(TESTING_VALUES_SMALL)
        assert all(
            len(returned.get("data").get(typ.lower())) == len(TESTING_VALUES_SMALL)
            for typ in DISTRIBUTION_COLORS
        )

    def test_utils_charts_distribution_chart_data_returns_limited_size(self):
        values = [
            [800, 312769, 26872283825, {}, 0],
            [600, 31566704, 30000000000, {}, 0],
            [200, 319473667, 625000000, {}, 0],
            [100, 508, 20000000, {}, 0],
            [10, 329110405, 20000000, {}, 0],
        ]
        consolidated_data = Consolidated(
            {312769: 100, 31566704: 300, 319473667: 50, 508: 0, 329110405: 5},
            {312769: 400, 31566704: 50, 319473667: 150, 508: 00, 329110405: 0},
            {312769: 200, 31566704: 150, 319473667: 0, 508: 50, 329110405: 0},
            {312769: 100, 31566704: 100, 319473667: 0, 508: 50, 329110405: 5},
            {312769: 500, 31566704: 200, 319473667: 200, 508: 400, 329110405: 500},
        )
        hide_last_percent = 0.1
        with mock.patch("utils.charts.HIDE_LAST_PERCENT", hide_last_percent):
            returned = _distribution_chart_data(TESTING_ASAS, values, consolidated_data)
        assert len(returned.get("labels")) == 4
        assert all(
            len(returned.get("data").get(typ.lower())) == 4
            for typ in DISTRIBUTION_COLORS
        )
        assert returned.get("labels")[-1] == "others"
        assert sum(
            float(val)
            for typ in DISTRIBUTION_COLORS
            for val in returned.get("data").get(typ.lower())
        ) == sum(value[0] for value in values)

    # # _distribution_chart_data_from_assets_data
    def test_utils_charts_distribution_chart_data_from_assets_data_for_zero_sum(
        self, mocker
    ):
        header1, header2, header3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        header1.total = 0
        header2.total = 0
        header3.total = 0
        assets_data = {
            "asa": [{"header": header1}, {"header": header2}, {"header": header3}]
        }
        returned = _distribution_chart_data_from_assets_data(
            assets_data, mocker.MagicMock()
        )
        assert returned == {}

    def test_utils_charts_distribution_chart_data_from_assets_data_returns_same_size_list(
        self, mocker
    ):
        header1, header2, header3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        header1.total = 70
        header2.total = 20
        header3.total = 10
        info1, info2, info3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        info1.id = 505
        info2.id = 506
        info3.id = 507
        assets_data = {
            "asa": [
                {"header": header1, "info": info1},
                {"header": header2, "info": info2},
                {"header": header3, "info": info3},
            ]
        }
        consolidated_data = Consolidated(
            {505: 100, 506: 200, 507: 300},
            {505: 1000, 506: 2000, 507: 3000},
            {505: 2000, 506: 1200, 507: 4300},
            {505: 4100, 506: 2500, 507: 800},
            {},
        )
        returned = _distribution_chart_data_from_assets_data(
            assets_data, consolidated_data
        )
        assert isinstance(returned.get("labels"), list)
        assert isinstance(returned.get("data"), dict)
        assert len(returned.get("labels")) == 3
        assert all(
            len(returned.get("data").get(typ.lower())) == 3
            for typ in DISTRIBUTION_COLORS
        )

    def test_utils_charts_distribution_chart_data_from_assets_data_returns_limited_size(
        self, mocker
    ):
        header1, header2, header3, header4, header5 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        header1.total = 900
        header2.total = 800
        header3.total = 700
        header4.total = 20
        header5.total = 10
        info1, info2, info3, info4, info5 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        info1.id = 505
        info2.id = 506
        info3.id = 507
        info4.id = 508
        info5.id = 509
        assets_data = {
            "asa": [
                {"header": header1, "info": info1},
                {"header": header2, "info": info2},
                {"header": header3, "info": info3},
                {"header": header4, "info": info4},
                {"header": header5, "info": info5},
            ]
        }
        consolidated_data = Consolidated(
            {505: 100, 506: 200, 507: 300},
            {505: 1000, 506: 2000, 507: 3000},
            {505: 2000, 506: 1200, 507: 4300},
            {505: 4100, 506: 2500, 507: 800},
            {},
        )
        hide_last_percent = 0.1
        with mock.patch("utils.charts.HIDE_LAST_PERCENT", hide_last_percent):
            returned = _distribution_chart_data_from_assets_data(
                assets_data, consolidated_data
            )
        assert len(returned.get("labels")) == 4
        assert all(
            len(returned.get("data").get(typ.lower())) == 4
            for typ in DISTRIBUTION_COLORS
        )
        assert returned.get("labels")[-1] == "others"
        assert (
            sum(
                float(val)
                for typ in DISTRIBUTION_COLORS
                for val in returned.get("data").get(typ.lower())
            )
            == 21500
        )

    # # _distribution_chart_from_assets_data
    def test_utils_charts_distribution_chart_from_assets_data_functionality(
        self, mocker
    ):
        mocked_setup = mocker.patch("utils.charts._distribution_setup")
        mocked_distribution = mocker.patch(
            "utils.charts._distribution_chart_data_from_assets_data",
            return_value={"a": "b"},
        )
        assets_data, consolidated_data = mocker.MagicMock(), mocker.MagicMock()
        returned = _distribution_chart_from_assets_data(assets_data, consolidated_data)
        assert returned == mocked_setup.return_value
        mocked_distribution.assert_called_once_with(assets_data, consolidated_data)
        mocked_setup.assert_called_once_with(a="b")

    # # _distribution_setup
    def test_utils_charts_distribution_setup_for_empty_labels_and_data(self):
        returned = _distribution_setup(labels=[], data={})
        assert returned == {
            "labels": [],
            "datasets": [
                {
                    "label": typ,
                    "data": [],
                    "backgroundColor": color,
                    "borderWidth": 0,
                    "hoverOffset": 0,
                }
                for typ, color in DISTRIBUTION_COLORS.items()
            ],
        }

    def test_utils_charts_distribution_setup_functionality(self):
        labels = ["ALGO", "ASASTATS", "USDC"]
        data = {
            "balance": [100, 200, 300],
            "staked": [0, 800, 0],
            "liquidity": [1000, 0, 10],
            "defi": [2500, 0, 100],
        }
        returned = _distribution_setup(labels=labels, data=data)
        assert returned == {
            "labels": labels,
            "datasets": [
                {
                    "label": typ,
                    "data": data.get(typ.lower()),
                    "backgroundColor": color,
                    "borderWidth": 0,
                    "hoverOffset": 0,
                }
                for typ, color in DISTRIBUTION_COLORS.items()
            ],
        }

    # # _nft_chart
    def test_utils_charts_nft_chart_for_provided_label(self, mocker):
        mocked_setup = mocker.patch("utils.charts._chart_setup")
        mocked_base = mocker.patch(
            "utils.charts._base_chart_data", return_value={"a": "b"}
        )
        nft_values, nft_colors = mocker.MagicMock(), mocker.MagicMock()
        returned = _nft_chart(nft_values, nft_colors, label="label")
        assert returned == mocked_setup.return_value
        mocked_base.assert_called_once_with(
            {},
            nft_values,
            nft_colors,
            distinct_colors=DISTINCT_COLORS_2,
            val_check=False,
        )
        mocked_setup.assert_called_once_with("label", a="b")

    def test_utils_charts_nft_chart_functionality(self, mocker):
        mocked_setup = mocker.patch("utils.charts._chart_setup")
        mocked_base = mocker.patch(
            "utils.charts._base_chart_data", return_value={"a": "b"}
        )
        nft_values, nft_colors = mocker.MagicMock(), mocker.MagicMock()
        returned = _nft_chart(nft_values, nft_colors)
        assert returned == mocked_setup.return_value
        mocked_base.assert_called_once_with(
            {},
            nft_values,
            nft_colors,
            distinct_colors=DISTINCT_COLORS_2,
            val_check=False,
        )
        mocked_setup.assert_called_once_with("NFT data", a="b")

    # # _nft_chart_from_assets_data
    def test_utils_charts_nft_chart_from_assets_data_for_provided_label(self, mocker):
        mocked_setup = mocker.patch("utils.charts._chart_setup")
        mocked_base = mocker.patch(
            "utils.charts._base_chart_data_from_assets_data", return_value={"a": "b"}
        )
        nft_data, nft_colors = mocker.MagicMock(), mocker.MagicMock()
        returned = _nft_chart_from_assets_data(nft_data, nft_colors, label="label")
        assert returned == mocked_setup.return_value
        mocked_base.assert_called_once_with(
            nft_data,
            nft_colors,
            distinct_colors=DISTINCT_COLORS_2,
        )
        mocked_setup.assert_called_once_with("label", a="b")

    def test_utils_charts_nft_chart_from_assets_data_functionality(self, mocker):
        mocked_setup = mocker.patch("utils.charts._chart_setup")
        mocked_base = mocker.patch(
            "utils.charts._base_chart_data_from_assets_data", return_value={"a": "b"}
        )
        nft_data, nft_colors = mocker.MagicMock(), mocker.MagicMock()
        returned = _nft_chart_from_assets_data(nft_data, nft_colors)
        assert returned == mocked_setup.return_value
        mocked_base.assert_called_once_with(
            nft_data, nft_colors, distinct_colors=DISTINCT_COLORS_2
        )
        mocked_setup.assert_called_once_with("NFT data", a="b")

    # #_ratio_chart
    def test_utils_charts_ratio_chart_calls_ratio_chart_data(self, mocker):
        mocker.patch("utils.charts._chart_setup")
        mocked = mocker.patch("utils.charts._ratio_chart_data", return_value={})
        total, consolidated_totals = mocker.MagicMock(), mocker.MagicMock()
        _ratio_chart(total, consolidated_totals)
        mocked.asset_called_once()
        mocked.asset_called_with(total, consolidated_totals)

    def test_utils_charts_ratio_chart_calls_end_returns_chart_setup(self, mocker):
        mocked_ratio = mocker.patch("utils.charts._ratio_chart_data", return_value={})
        mocked = mocker.patch("utils.charts._chart_setup")
        returned = _ratio_chart(mocker.MagicMock(), mocker.MagicMock())
        mocked.asset_called_once()
        mocked.asset_called_with("Ratio data", mocked_ratio.return_value)
        assert returned == mocked.return_value

    # # _ratio_chart_data
    def test_utils_charts_ratio_chart_data_returns_empty_dict_for_total_zero(
        self, mocker
    ):
        total = Total(1, 1, 1, 0, 1, 1, 1, 1)
        returned = _ratio_chart_data(total, mocker.MagicMock())
        assert returned == {}

    def test_utils_charts_ratio_chart_data_functionality(self):
        total = Total(1, 1, 500, 2300, 1, 1, 1, 1)
        consolidated_totals = (100, 200, 500, 1000, 2000)
        returned = _ratio_chart_data(total, consolidated_totals)
        assert returned == {
            "labels": [typ for typ in DISTRIBUTION_COLORS] + ["NFT"],
            "data": [
                "4.34782609",
                "8.69565217",
                "21.73913043",
                "43.47826087",
                "21.73913043",
            ],
            "colors": [color for color in DISTRIBUTION_COLORS.values()]
            + [CHART_NFT_COLOR],
        }

    @pytest.mark.parametrize(
        "total,result",
        [
            (
                Total(1, 1, 500, 3300, 1, 1, 1, 1),
                [
                    "3.03030303",
                    "6.06060606",
                    "15.15151515",
                    "30.30303030",
                    "15.15151515",
                ],
            ),
            (
                Total(1, 1, 400, 2300, 1, 1, 1, 1),
                [
                    "4.34782609",
                    "8.69565217",
                    "21.73913043",
                    "43.47826087",
                    "17.39130435",
                ],
            ),
            (
                Total(1, 1, 800, 4500, 1, 1, 1, 1),
                [
                    "2.22222222",
                    "4.44444444",
                    "11.11111111",
                    "22.22222222",
                    "17.77777778",
                ],
            ),
            (
                Total(1, 1, 700, 5000, 1, 1, 1, 1),
                [
                    "2.00000000",
                    "4.00000000",
                    "10.00000000",
                    "20.00000000",
                    "14.00000000",
                ],
            ),
            (
                Total(1, 1, 100, 2000, 1, 1, 1, 1),
                [
                    "5.00000000",
                    "10.00000000",
                    "25.00000000",
                    "50.00000000",
                    "5.00000000",
                ],
            ),
            (
                Total(1, 1, 1000, 2000, 1, 1, 1, 1),
                [
                    "5.00000000",
                    "10.00000000",
                    "25.00000000",
                    "50.00000000",
                    "50.00000000",
                ],
            ),
        ],
    )
    def test_utils_charts_ratio_chart_data_returns_data_from_total(self, total, result):
        consolidated_totals = (100, 200, 500, 1000, 2000)
        returned = _ratio_chart_data(total, consolidated_totals)
        assert returned.get("data") == result

    def test_utils_charts_ratio_chart_data_returns_colors(self):
        total = Total(1, 1, 1, 1, 1, 1, 1, 1)
        consolidated_totals = (100, 200, 500, 1000, 2000)
        returned = _ratio_chart_data(total, consolidated_totals)
        assert returned.get("colors") == [
            color for color in DISTRIBUTION_COLORS.values()
        ] + [CHART_NFT_COLOR]


class TestUtilsChartPublicFunctions:
    """Testing class for :py:mod:`utils.charts` public functions."""

    # # prepare_base_charts
    def test_utils_charts_prepare_base_charts_functionality(self, mocker):
        mocked_asa = mocker.patch("utils.charts._asa_chart")
        mocked_nft = mocker.patch("utils.charts._nft_chart")
        asas, values, nft_values = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        returned = prepare_base_charts(asas, values, nft_values)
        assert returned == (
            mocked_asa.return_value,
            mocked_nft.return_value,
            {0: "algo"},
            {},
        )
        mocked_asa.assert_called_once_with(asas, values, {0: "algo"})
        mocked_nft.asset_called_with(nft_values, {})

    # # prepare_base_charts_from_assets_data
    def test_utils_charts_prepare_base_charts_from_assets_data_functionality(
        self, mocker
    ):
        mocked_asa = mocker.patch("utils.charts._asa_chart_from_assets_data")
        mocked_nft = mocker.patch("utils.charts._nft_chart_from_assets_data")
        asa, nft = mocker.MagicMock(), mocker.MagicMock()
        assets_data = {"asa": asa, "nft": nft}
        returned = prepare_base_charts_from_assets_data(assets_data)
        assert returned == (
            mocked_asa.return_value,
            mocked_nft.return_value,
            {0: "algo"},
            {},
        )
        mocked_asa.assert_called_once_with(asa, {0: "algo"})
        mocked_nft.asset_called_with(nft, {})

    # # prepare_base_charts_from_serialized_data
    def test_utils_charts_prepare_base_charts_from_serialized_data_functionality(
        self, mocker
    ):
        mocked_asa = mocker.patch("utils.charts._asa_chart_from_serialized_data")
        mocked_nft = mocker.patch("utils.charts._nft_chart_from_serialized_data")
        serialized_data = mocker.MagicMock()
        returned = prepare_base_charts_from_serialized_data(serialized_data)
        assert returned == (
            mocked_asa.return_value,
            mocked_nft.return_value,
            {0: "algo"},
            {},
        )
        mocked_asa.assert_called_once_with(serialized_data, {0: "algo"})
        mocked_nft.assert_called_once_with(serialized_data, {})


# # INTEGRATION
class TestSerializedChartsAgainstSamplePayload:
    """End-to-end smoke test using a real API 2.0 response.

    Locks in structural invariants we'd want to catch breaking during the
    Phase 1 view rewrite or any future API serializer change.

    The captured payload (``sample_serialized_540A5.json``) is a bundle of two
    addresses with 76 asaitems, 55 NFT collections, and 1 noteval. The numbers
    asserted here come from rendering the same data through these helpers and
    spot-checking against the source JSON, so they document expected behavior
    on real data rather than a contrived fixture.
    """

    def test_base_charts_return_well_formed_structures(self, sample_payload):
        asachart, nftchart, asa_colors, nft_colors = (
            prepare_base_charts_from_serialized_data(sample_payload)
        )

        # Both charts have the _chart_setup shape.
        for chart in (asachart, nftchart):
            assert set(chart.keys()) == {"labels", "datasets"}
            assert len(chart["datasets"]) == 1
            ds = chart["datasets"][0]
            assert set(ds.keys()) == {
                "label",
                "data",
                "backgroundColor",
                "borderWidth",
                "hoverOffset",
            }
            assert len(ds["data"]) == len(chart["labels"])
            assert len(ds["backgroundColor"]) == len(chart["labels"])

        assert asachart["datasets"][0]["label"] == "ASA data"
        assert nftchart["datasets"][0]["label"] == "NFT data"

    def test_asachart_top_label_matches_highest_valued_asaitem(self, sample_payload):
        # The first asaitem in the sample is LFTY0046 at 253.7 ALGO.
        asachart, *_ = prepare_base_charts_from_serialized_data(sample_payload)
        assert asachart["labels"][0] == "LFTY0046"

    def test_asachart_percentages_sum_to_one_hundred(self, sample_payload):
        asachart, *_ = prepare_base_charts_from_serialized_data(sample_payload)
        # Floatformat rounding allows a tiny epsilon.
        assert sum(float(d) for d in asachart["datasets"][0]["data"]) == pytest.approx(
            100.0, abs=0.01
        )

    def test_asa_colors_keyed_by_asset_id_with_algo_seeded(self, sample_payload):
        _asa, _nft, asa_colors, _nft_colors = prepare_base_charts_from_serialized_data(
            sample_payload
        )
        # ALGO (id=0) seed is overwritten during iteration to its positional slot;
        # this matches the legacy _base_chart_data behavior.
        assert 0 in asa_colors
        # LFTY0046 is at position 0 (top-valued).
        assert asa_colors[393401013] == "0"

    def test_consolidated_pipeline_runs_end_to_end(self, sample_payload):
        _asa, _nft, _asa_colors, nft_colors = prepare_base_charts_from_serialized_data(
            sample_payload
        )
        distchart, ratiochart, nftfloorchart, consolidated_totals = (
            prepare_consolidated_charts_from_serialized_data(sample_payload, nft_colors)
        )

        # Distribution chart: one dataset per DISTRIBUTION_COLORS segment.
        assert len(distchart["datasets"]) == len(DISTRIBUTION_COLORS)
        for ds in distchart["datasets"]:
            assert len(ds["data"]) == len(distchart["labels"])

        # Ratio chart: balance/staked/liquidity/defi plus NFT, percentages
        # summing to ~100.
        assert ratiochart["labels"] == [
            *DISTRIBUTION_COLORS.keys(),
            "NFT",
        ]
        ratio_total = sum(float(d) for d in ratiochart["datasets"][0]["data"])
        assert ratio_total == pytest.approx(100.0, abs=0.01)

        # NFT floor chart: one row per collection with a floor price.
        assert nftfloorchart["datasets"][0]["label"] == "NFT floor data"
        assert len(nftfloorchart["labels"]) > 0

        # Consolidated totals: positive numbers across the board.
        assert isinstance(consolidated_totals, Consolidated)
        assert consolidated_totals.balance > 0
        assert consolidated_totals.staked > 0
        assert consolidated_totals.liquidity > 0
        assert consolidated_totals.defi > 0
        assert consolidated_totals.nftfloor > 0

    def test_consolidated_totals_match_sum_of_segments(self, sample_payload):
        # The consolidated_totals returned by the public function should equal
        # the sum of the underlying per-asset segment dicts, since that's how
        # _consolidated_totals_from_consolidated_data computes them.
        _asa, _nft, _asa_colors, nft_colors = prepare_base_charts_from_serialized_data(
            sample_payload
        )
        _dist, _ratio, _nftfloor, consolidated_totals = (
            prepare_consolidated_charts_from_serialized_data(sample_payload, nft_colors)
        )
        # Pull balance directly via the underlying serialized helper and
        # check it matches the totals struct.
        from utils.charts import _balance_totals_from_serialized_data

        expected_balance = sum(
            _balance_totals_from_serialized_data(sample_payload).values()
        )
        assert consolidated_totals.balance == pytest.approx(expected_balance)

    def test_ratio_chart_nft_segment_matches_total_struct(self, sample_payload):
        # The NFT slice of the ratio chart should be 100 * total.nft / total.total
        # — i.e. the percent of the portfolio's value that's in NFTs.
        _asa, _nft, _asa_colors, nft_colors = prepare_base_charts_from_serialized_data(
            sample_payload
        )
        _dist, ratiochart, _nftfloor, _totals = (
            prepare_consolidated_charts_from_serialized_data(sample_payload, nft_colors)
        )
        total = _total_from_serialized_data(sample_payload)
        expected_nft_pct = 100 * total.nft / total.total
        nft_pct = float(ratiochart["datasets"][0]["data"][-1])
        assert nft_pct == pytest.approx(expected_nft_pct, abs=1e-6)

    def test_nft_collection_colors_seed_nft_colors_dict(self, sample_payload):
        _asa, _nft, _asa_colors, nft_colors = prepare_base_charts_from_serialized_data(
            sample_payload
        )
        # NFT colors are keyed by collection name (not by asset id), since
        # collections aren't single assets.
        assert all(isinstance(k, str) for k in nft_colors)
        assert len(nft_colors) > 0
