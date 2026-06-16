"""Module containing chart creating functions."""

from collections import defaultdict

from django.template.defaultfilters import floatformat

from utils.constants.charts import (
    ASASTATS_COLOR_OTHERS,
    CHART_NFT_COLOR,
    DISTINCT_COLORS,
    DISTINCT_COLORS_2,
    DISTRIBUTION_COLORS,
    HIDE_LAST_PERCENT,
    PIE_CHART_MAXIMUM_ITEMS,
)
from utils.constants.core import ALGO_ID
from utils.structs import Consolidated, Total


def _asa_chart(asas, values, asa_colors):
    """Prepare and return ASA chart.

    :param asas: collection of assets immutable data
    :type asas: dict
    :param values: collection of amounts related to asset
    :type values: list
    :param asa_colors: collection of asset ids and related CSS color prefixes
    :type asa_colors: dict
    :return: dict
    """
    return _chart_setup("ASA data", **_base_chart_data(asas, values, asa_colors))


def _asa_chart_from_assets_data(asa_data, asa_colors):
    """Prepare and return ASA chart.

    :param asa_data: processed ASA section data ready for rendering
    :type asa_data: dict
    :param asa_colors: collection of asset ids and related CSS color prefixes
    :type asa_colors: dict
    :return: dict
    """
    return _chart_setup(
        "ASA data", **_base_chart_data_from_assets_data(asa_data, asa_colors)
    )


def _assign_nftfloor_colors(nftfloor_chart, nft_colors):
    """Update provided NFT floor chart data with correct NFT collection colors.

    :param nftfloor_chart: NFT floor chart data
    :type nftfloor_chart: dict
    :param nft_colors: collection of NFT collections and related CSS color prefixes
    :type nft_colors: dict
    """
    nftfloor_chart["datasets"][0]["backgroundColor"] = [
        (
            DISTINCT_COLORS_2[int(nft_colors.get(collection))]
            if nft_colors.get(collection) is not None
            else ASASTATS_COLOR_OTHERS
        )
        for collection in nftfloor_chart.get("labels", [])
    ]


def _base_chart_data(
    asas, values, asa_colors, distinct_colors=DISTINCT_COLORS, val_check=True
):
    """Prepare and return data for ASA and NFT charts.

    :param asas: collection of assets immutable data
    :type asas: dict
    :param values: collection of amounts related to asset
    :type values: :class:`utils.structs.Values`
    :param asa_colors: collection of asset ids and related CSS color prefixes
    :type asa_colors: dict
    :param distinct_colors: collection of CSS colors
    :type distinct_colors: dict
    :var asasum: total value in ALGO of all ASA and ALGO
    :type asasum: float
    :var limit: percentage limit for asa to be shown in graph
    :type limit: float
    :var total: current sum in Algos
    :type total: float
    :var labels: items labels collection
    :type labels: list
    :var data: chart data collection
    :type data: list
    :var colors: items colors collection
    :type colors: list
    :var count: total number of values items having value
    :type count: int
    :var rows: non-zero valued rows from values
    :type rows: int
    :return: dict
    """
    asasum = sum(val[0] for val in values if val[0] > 0)  #  and val[1] != 0

    if not asasum > 0:
        return {}

    limit = (1.0 - HIDE_LAST_PERCENT) * asasum
    total = 0
    labels = []
    data = []
    colors = []

    if val_check:
        count = sum(1 for val in values if val[0] > 0)  #  and val[1] != 0
    else:
        count = sum(1 for _ in values)

    if val_check:
        rows = [val for val in values if val[0] > 0]  #  and val[1] != 0
    else:
        rows = [val for val in values]

    for i, value in enumerate(rows):
        unit = asas.get(value[1]).unit if asas.get(value[1]) else value[1] or "ALGO"
        labels.append(unit)
        data.append(floatformat(100 * (value[0] / asasum), 8))
        colors.append(distinct_colors[i])
        asa_colors[value[1]] = str(i)
        total += value[0]
        if i == count - 1:
            break

        if i < count - 2 and (total > limit or i > PIE_CHART_MAXIMUM_ITEMS - 2):
            labels.append("others")
            data.append(floatformat(100 * ((asasum - total) / asasum), 8))
            colors.append(ASASTATS_COLOR_OTHERS)
            break

    return {"labels": labels, "data": data, "colors": colors}


def _base_chart_data_from_assets_data(
    asset_data, asa_colors, distinct_colors=DISTINCT_COLORS
):
    """Prepare and return data for ASA and NFT charts.

    :param asset_data: processed ASA/NFT section data ready for rendering
    :type asset_data: dict
    :param asa_colors: collection of asset ids and related CSS color prefixes
    :type asa_colors: dict
    :param distinct_colors: collection of CSS colors
    :type distinct_colors: dict
    :var section_total: total section value in ALGO
    :type section_total: float
    :var limit: percentage limit for asa to be shown in graph
    :type limit: float
    :var total: current sum in Algos
    :type total: float
    :var labels: items labels collection
    :type labels: list
    :var data: chart data collection
    :type data: list
    :var colors: items colors collection
    :type colors: list
    :var count: total number of values items having value
    :type count: int
    :var item: currently processed custom element instance
    :type item: int
    :var unit: currently processed element's unit
    :type unit: str
    :return: dict
    """
    section_total = sum(item.get("header").total for item in asset_data)

    if not section_total > 0:
        return {}

    limit = (1.0 - HIDE_LAST_PERCENT) * section_total
    total = 0
    labels = []
    data = []
    colors = []

    count = len(asset_data)

    for i, item in enumerate(asset_data):
        unit = item.get("header").label
        labels.append(unit)
        data.append(floatformat(100 * (item.get("header").total / section_total), 8))
        colors.append(distinct_colors[i])
        asa_colors[item.get("header").label] = str(i)
        total += item.get("header").total
        if i == count - 1:
            break

        if i < count - 2 and (total > limit or i > PIE_CHART_MAXIMUM_ITEMS - 2):
            labels.append("others")
            data.append(floatformat(100 * ((section_total - total) / section_total), 8))
            colors.append(ASASTATS_COLOR_OTHERS)
            break

    return {"labels": labels, "data": data, "colors": colors}


def _chart_setup(label, labels=[], data=[], colors=[]):
    """Return chart data populated from provided arguments.

    :param label: chart's main label
    :type label: str
    :param labels: collection of chart elements names
    :type labels: list
    :param data: collection of chart elements percentage values
    :type data: list
    :param colors: collection of chart elements background colors
    :type colors: list
    :return: dict
    """
    return {
        "labels": labels,
        "datasets": [
            {
                "label": label,
                "data": data,
                "backgroundColor": colors,
                "borderWidth": 1,
                "hoverOffset": 0,
            }
        ],
    }


def _distribution_chart(asas, values, consolidated_data):
    """Prepare and return top assets distribution chart from provided data.

    :param asas: collection of assets immutable data
    :type asas: dict
    :param values: collection of amounts and data related to asset
    :type values: list
    :param consolidated_data: all the data needed for consolidated view
    :type consolidated_data: :class:`utils.structs.Consolidated`
    :return: dict
    """
    return _distribution_setup(
        **_distribution_chart_data(asas, values, consolidated_data),
    )


def _distribution_chart_data(asas, values, consolidated_data):
    """Prepare and return data for ASA and NFT charts.

    TODO: refactor

    :param asas: collection of assets immutable data
    :type asas: dict
    :param values: collection of amounts related to asset
    :type values: :class:`utils.structs.Values`
    :param consolidated_data: all the data needed for consolidated view
    :type consolidated_data: :class:`utils.structs.Consolidated`
    :var section_total: total section value in ALGO
    :type section_total: float
    :var limit: percentage limit for asa to be shown in graph
    :type limit: float
    :var total: current sum in Algos
    :type total: float
    :var labels: items labels collection
    :type labels: list
    :var data: chart data collection
    :type data: list
    :var segments: collection of distribution type names
    :type segments: list
    :var count: total number of values items having value
    :type count: int
    :var rows: non-zero valued rows from values
    :type rows: int
    :return: dict
    """
    section_total = sum(val[0] for val in values if val[0] > 0)

    if not section_total > 0:
        return {}

    limit = (1.0 - HIDE_LAST_PERCENT) * section_total
    total = 0
    labels = []
    data = defaultdict(list)
    segments = [name.lower() for name in DISTRIBUTION_COLORS]

    count = sum(1 for val in values if val[0] > 0)
    rows = [val for val in values if val[0] > 0]

    for i, value in enumerate(rows):
        unit = asas.get(value[1]).unit if asas.get(value[1]) else value[1] or "ALGO"
        labels.append(unit)
        for segment in segments:
            data[segment].append(
                floatformat(getattr(consolidated_data, segment).get(value[1], 0), 8)
            )
        total += value[0]
        if i == count - 1:
            break

        if i < count - 2 and (total > limit or i > PIE_CHART_MAXIMUM_ITEMS - 2):
            labels.append("others")
            for segment in segments:
                segment_total = sum(
                    getattr(consolidated_data, segment).get(value[1], 0)
                    for value in rows[i + 1 :]
                )
                data[segment].append(floatformat(segment_total, 8))
            break

    return {"labels": labels, "data": data}


def _distribution_chart_data_from_assets_data(assets_data, consolidated_data):
    """Prepare and return data for ASA and NFT charts.

    TODO: refactor

    :param assets_data: processed asset section data ready for rendering
    :type assets_data: dict
    :param consolidated_data: all the data needed for consolidated view
    :type consolidated_data: :class:`utils.structs.Consolidated`
    :var section_total: total section value in ALGO
    :type section_total: float
    :var limit: percentage limit for asa to be shown in graph
    :type limit: float
    :var total: current sum in Algos
    :type total: float
    :var labels: items labels collection
    :type labels: list
    :var data: chart data collection
    :type data: list
    :var segments: collection of distribution type names
    :type segments: list
    :var count: total number of values items having value
    :type count: int
    :var rows: non-zero valued rows from values
    :type rows: int
    :var item: currently processed asset's custom object
    :type item: dict
    :var unit: currently processed asset unit
    :type unit: str
    :var segment: currently processed distribution type name
    :type segment: str
    :var segment_total: currently processed segment's total
    :type segment_total: float
    :return: dict
    """
    section_total = sum(
        item.get("header").total
        for item in assets_data.get("asa", [])
        if item.get("header").total
    )

    if not section_total > 0:
        return {}

    limit = (1.0 - HIDE_LAST_PERCENT) * section_total
    total = 0
    labels = []
    data = defaultdict(list)
    segments = [name.lower() for name in DISTRIBUTION_COLORS]

    count = len(assets_data.get("asa", []))
    rows = [item for item in assets_data.get("asa", [])]

    for i, item in enumerate(assets_data.get("asa")):
        unit = item.get("info").unit
        labels.append(unit)
        for segment in segments:
            data[segment].append(
                floatformat(
                    getattr(consolidated_data, segment).get(item.get("info").id, 0), 8
                )
            )
        total += item.get("header").total
        if i == count - 1:
            break

        if i < count - 2 and (total > limit or i > PIE_CHART_MAXIMUM_ITEMS - 2):
            labels.append("others")
            for segment in segments:
                segment_total = sum(
                    getattr(consolidated_data, segment).get(_item.get("info").id, 0)
                    for _item in rows[i + 1 :]
                )
                data[segment].append(floatformat(segment_total, 8))
            break

    return {"labels": labels, "data": data}


def _distribution_chart_from_assets_data(assets_data, consolidated_data):
    """Prepare and return top assets distribution chart from provided data.

    :param assets_data: processed asset section data ready for rendering
    :type assets_data: dict
    :param consolidated_data: all the data needed for consolidated view
    :type consolidated_data: :class:`utils.structs.Consolidated`
    :return: dict
    """
    return _distribution_setup(
        **_distribution_chart_data_from_assets_data(assets_data, consolidated_data),
    )


def _distribution_setup(labels=[], data={}):
    """Return distribution chart data populated from provided arguments.

    :param labels: collection of chart elements names
    :type labels: list
    :param data: collection of distribution types percentage values
    :type data: dict
    :return: dict
    """
    return {
        "labels": labels,
        "datasets": [
            {
                "label": typ,
                "data": data.get(typ.lower(), []),
                "backgroundColor": color,
                "borderWidth": 0,
                "hoverOffset": 0,
            }
            for typ, color in DISTRIBUTION_COLORS.items()
        ],
    }


def _nft_chart(nft_values, nft_colors, label="NFT data"):
    """Prepare and return NFT chart.

    :param nft_values: collection of amounts and data related to NFT
    :type nft_values: list
    :param nft_colors: collection of NFT ids and related CSS color prefixes
    :type nft_colors: dict
    :param label: chart label text
    :type label: str
    :return: dict
    """
    return _chart_setup(
        label,
        **_base_chart_data(
            {},
            nft_values,
            nft_colors,
            distinct_colors=DISTINCT_COLORS_2,
            val_check=False,
        ),
    )


def _nft_chart_from_assets_data(nft_data, nft_colors, label="NFT data"):
    """Prepare and return NFT chart.

    :param nft_data: processed NFT section data ready for rendering
    :type nft_data: dict
    :param nft_colors: collection of NFT ids and related CSS color prefixes
    :type nft_colors: dict
    :param label: chart label text
    :type label: str
    :return: dict
    """
    return _chart_setup(
        label,
        **_base_chart_data_from_assets_data(
            nft_data, nft_colors, distinct_colors=DISTINCT_COLORS_2
        ),
    )


def _ratio_chart(total, consolidated_totals):
    """Prepare and return ratio chart.

    :param total: totals collection
    :type total: :class:`Total`
    :var consolidated_totals: consolidated view totals
    :type consolidated_totals: :class:`utils.structs.Consolidated`
    :return: dict
    """
    return _chart_setup("Ratio data", **_ratio_chart_data(total, consolidated_totals))


def _ratio_chart_data(total, consolidated_totals):
    """Prepare and return data for ratio chart.

    :param total: totals collection
    :type total: :class:`Total`
    :var consolidated_totals: consolidated view totals
    :type consolidated_totals: :class:`utils.structs.Consolidated`
    :return: dict
    """
    return (
        {}
        if total.total == 0
        else {
            "labels": [typ for typ in DISTRIBUTION_COLORS] + ["NFT"],
            "data": [
                floatformat(100 * (section / total.total), 8)
                for section in [*consolidated_totals[:-1], total.nft]
            ],
            "colors": [color for color in DISTRIBUTION_COLORS.values()]
            + [CHART_NFT_COLOR],
        }
    )


# # CONSOLIDATED
def _asa_chart_from_serialized_data(serialized_data, asa_colors):
    """Prepare and return ASA chart from serialized account data.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param asa_colors: collection of asset ids and related CSS color prefixes
    :type asa_colors: dict
    :return: dict
    """
    return _chart_setup(
        "ASA data",
        **_base_chart_data_from_serialized_data(
            serialized_data.get("asaitems", []), asa_colors
        ),
    )


def _balance_totals_from_assets_data(assets_data):
    """Calculate and return collection of asset IDs and related balance values.

    :param assets_data: processed asset section data ready for rendering
    :type assets_data: dict
    :return: dict
    """
    return {
        asa.get("info").id: next(
            (elem.value for elem in asa.get("body", []) if elem.type == "Balance"), 0
        )
        for asa in assets_data.get("asa", [])
    }


def _balance_totals_from_serialized_data(serialized_data):
    """Calculate and return collection of asset IDs and related balance values.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :return: dict
    """
    return {
        asaitem.get("asset").get("id"): next(
            (
                float(program.get("value", 0))
                for program in asaitem.get("programs", [])
                if program.get("program").get("type") == "Balance"
            ),
            0,
        )
        for asaitem in serialized_data.get("asaitems", [])
    }


def _base_chart_data_from_serialized_data(
    asaitems, asa_colors, distinct_colors=DISTINCT_COLORS, val_check=True
):
    """Prepare and return data for ASA and NFT charts from serialized asaitems.

    Mirrors :func:`_base_chart_data` for the API 2.0 serialized data shape.

    :param asaitems: collection of serialized asaitems or nftcollections
    :type asaitems: list
    :param asa_colors: collection of asset ids and related CSS color prefixes
    :type asa_colors: dict
    :param distinct_colors: collection of CSS colors
    :type distinct_colors: tuple
    :param val_check: whether to filter rows by ``float(value) > 0``
    :type val_check: bool
    :var asasum: total value in ALGO of all rows
    :type asasum: float
    :var limit: percentage limit for asset to be shown in graph
    :type limit: float
    :var rows: filtered rows from asaitems
    :type rows: list
    :var count: total number of rows to consider
    :type count: int
    :var labels: items labels collection
    :type labels: list
    :var data: chart data collection
    :type data: list
    :var colors: items colors collection
    :type colors: list
    :return: dict
    """
    if val_check:
        rows = [item for item in asaitems if float(item.get("value", 0)) > 0]
    else:
        rows = list(asaitems)

    asasum = sum(float(item.get("value", 0)) for item in rows)

    if not asasum > 0:
        return {}

    limit = (1.0 - HIDE_LAST_PERCENT) * asasum
    total = 0
    labels = []
    data = []
    colors = []
    count = len(rows)

    for i, item in enumerate(rows):
        is_nft_collection = "asset" not in item
        if is_nft_collection:
            unit = item.get("name") or ""
            key = unit
        else:
            unit = _unit_for_asaitem(item)
            key = item.get("asset", {}).get("id")

        value = float(item.get("value", 0))
        labels.append(unit)
        data.append(floatformat(100 * (value / asasum), 8))
        colors.append(distinct_colors[i])
        asa_colors[key] = str(i)
        total += value

        if i == count - 1:
            break

        if i < count - 2 and (total > limit or i > PIE_CHART_MAXIMUM_ITEMS - 2):
            labels.append("others")
            data.append(floatformat(100 * ((asasum - total) / asasum), 8))
            colors.append(ASASTATS_COLOR_OTHERS)
            break

    return {"labels": labels, "data": data, "colors": colors}


def _consolidated_data_from_assets_data(assets_data):
    """Prepare and return all the data needed for consolidated view.

    :param assets_data: processed asset section data ready for rendering
    :type assets_data: dict
    :var balance_values: collection of asset IDs and related balance values
    :type balance_values: dict
    :var staked_values: collection of asset IDs and related staked values
    :type staked_values: dict
    :var liquidity_values: collection of asset IDs and related liquidity values
    :type liquidity_values: dict
    :var defi_values: collection of asset IDs and related DeFi values
    :type defi_values: dict
    :return: :class:`utils.structs.Consolidated`
    """
    balance_values = _balance_totals_from_assets_data(assets_data)
    staked_values = _staked_totals_from_assets_data(assets_data)
    liquidity_values = _liquidity_totals_from_assets_data(assets_data)
    defi_values = _defi_totals_from_assets_data(assets_data)

    return Consolidated(
        balance_values, staked_values, liquidity_values, defi_values, ()
    )


def _consolidated_data_from_serialized_data(serialized_data):
    """Prepare and return all the data needed for consolidated view.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :var balance_values: collection of asset IDs and related balance values
    :type balance_values: dict
    :var staked_values: collection of asset IDs and related staked values
    :type staked_values: dict
    :var liquidity_values: collection of asset IDs and related liquidity values
    :type liquidity_values: dict
    :var defi_values: collection of asset IDs and related DeFi values
    :type defi_values: dict
    :var nftfloor_values: collection of NFT floor total values and NFT collection names
    :type nftfloor_values: list
    :return: :class:`utils.structs.Consolidated`
    """
    balance_values = _balance_totals_from_serialized_data(serialized_data)
    staked_values = _staked_totals_from_serialized_data(serialized_data)
    liquidity_values = _liquidity_totals_from_serialized_data(serialized_data)
    defi_values = _defi_totals_from_serialized_data(serialized_data)
    nftfloor_values = _nftfloor_totals_from_serialized_data(serialized_data)

    return Consolidated(
        balance_values, staked_values, liquidity_values, defi_values, nftfloor_values
    )


def _consolidated_totals_from_consolidated_data(consolidated_data):
    """Prepare and return consolidated view totals instance.

    :param consolidated_data: all the data for consolidated view
    :type consolidated_data: :class:`utils.structs.Consolidated`
    :var total_balance: sum of account's balance values
    :type total_balance: float
    :var total_staked: sum of account's staked values
    :type total_staked: float
    :var total_liquidity: sum of account's liquidity values
    :type total_liquidity: float
    :var total_defi: sum of account's DeFi values
    :type total_defi: float
    :var total_nft_floor: sum of account's NFT floor values
    :type total_nft_floor: float
    :return: :class:`utils.structs.Consolidated`
    """
    total_balance = sum(value for value in consolidated_data.balance.values())
    total_staked = sum(value for value in consolidated_data.staked.values())
    total_liquidity = sum(value for value in consolidated_data.liquidity.values())
    total_defi = sum(value for value in consolidated_data.defi.values())
    total_nftfloor = sum(row[0] for row in consolidated_data.nftfloor)

    return Consolidated(
        total_balance, total_staked, total_liquidity, total_defi, total_nftfloor
    )


def _defi_totals_from_assets_data(assets_data):
    """Calculate and return collection of asset IDs and related DeFi values.

    :param assets_data: processed asset section data ready for rendering
    :type assets_data: dict
    :return: dict
    """
    return {
        asa.get("info").id: sum(
            elem.value
            for elem in asa.get("body", [])
            if not (
                elem.type == "Balance"
                or (elem.type == "Staked" and "farm" not in elem.name)
                or (elem.source is not None and "LP" in elem.source)
            )
        )
        for asa in assets_data.get("asa", [])
    }


def _defi_totals_from_serialized_data(serialized_data):
    """Calculate and return collection of asset IDs and related DeFi values.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :return: dict
    """
    return {
        asaitem.get("asset").get("id"): sum(
            float(program.get("value", 0))
            for program in asaitem.get("programs", [])
            if not (
                program.get("program").get("type") == "Balance"
                or (
                    program.get("program").get("type") == "Staked"
                    and "farm" not in program.get("program").get("name")
                )
                or (
                    program.get("program").get("type") == "Added"
                    and program.get("program").get("name") == "Liquidity"
                )
            )
        )
        for asaitem in serialized_data.get("asaitems", [])
    }


def _distribution_chart_data_from_serialized_data(serialized_data, consolidated_data):
    """Prepare and return data for the distribution chart from serialized data.

    Mirrors :func:`_distribution_chart_data` for the API 2.0 serialized data shape.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param consolidated_data: all the data needed for consolidated view
    :type consolidated_data: :class:`utils.structs.Consolidated`
    :var asaitems: serialized asaitems collection
    :type asaitems: list
    :var section_total: total section value in ALGO
    :type section_total: float
    :var limit: percentage limit for asset to be shown in graph
    :type limit: float
    :var rows: non-zero valued rows from asaitems
    :type rows: list
    :var segments: collection of distribution type names
    :type segments: list
    :return: dict
    """
    asaitems = serialized_data.get("asaitems", [])
    rows = [item for item in asaitems if float(item.get("value", 0)) > 0]
    section_total = sum(float(item.get("value", 0)) for item in rows)

    if not section_total > 0:
        return {}

    limit = (1.0 - HIDE_LAST_PERCENT) * section_total
    total = 0
    labels = []
    data = defaultdict(list)
    segments = [name.lower() for name in DISTRIBUTION_COLORS]
    count = len(rows)

    for i, item in enumerate(rows):
        asset_id = item.get("asset", {}).get("id")
        labels.append(_unit_for_asaitem(item))
        for segment in segments:
            data[segment].append(
                floatformat(getattr(consolidated_data, segment).get(asset_id, 0), 8)
            )
        total += float(item.get("value", 0))

        if i == count - 1:
            break

        if i < count - 2 and (total > limit or i > PIE_CHART_MAXIMUM_ITEMS - 2):
            labels.append("others")
            for segment in segments:
                segment_total = sum(
                    getattr(consolidated_data, segment).get(
                        row.get("asset", {}).get("id"), 0
                    )
                    for row in rows[i + 1 :]
                )
                data[segment].append(floatformat(segment_total, 8))
            break

    return {"labels": labels, "data": data}


def _distribution_chart_from_serialized_data(serialized_data, consolidated_data):
    """Prepare and return distribution chart from serialized account data.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param consolidated_data: all the data needed for consolidated view
    :type consolidated_data: :class:`utils.structs.Consolidated`
    :return: dict
    """
    return _distribution_setup(
        **_distribution_chart_data_from_serialized_data(
            serialized_data, consolidated_data
        ),
    )


def _liquidity_totals_from_assets_data(assets_data):
    """Calculate and return collection of asset IDs and related liquidity values.

    :param assets_data: processed asset section data ready for rendering
    :type assets_data: dict
    :return: dict
    """
    return {
        asa.get("info").id: sum(
            elem.value
            for elem in asa.get("body", [])
            if elem.source is not None and "LP" in elem.source
        )
        for asa in assets_data.get("asa", [])
    }


def _liquidity_totals_from_serialized_data(serialized_data):
    """Calculate and return collection of asset IDs and related liquidity values.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :return: dict
    """
    return {
        asaitem.get("asset").get("id"): sum(
            float(program.get("value", 0))
            for program in asaitem.get("programs", [])
            if program.get("program").get("type") == "Added"
            and program.get("program").get("name") == "Liquidity"
        )
        for asaitem in serialized_data.get("asaitems", [])
    }


def _nft_chart_from_serialized_data(serialized_data, nft_colors, label="NFT data"):
    """Prepare and return NFT chart from serialized account data.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param nft_colors: collection of NFT collection names and related color prefixes
    :type nft_colors: dict
    :param label: chart label text
    :type label: str
    :return: dict
    """
    return _chart_setup(
        label,
        **_base_chart_data_from_serialized_data(
            serialized_data.get("nftcollections", []),
            nft_colors,
            distinct_colors=DISTINCT_COLORS_2,
            val_check=False,
        ),
    )


def _nftfloor_totals_from_serialized_data(serialized_data):
    """Calculate and return array of NFT collection floor totals and names.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :var nft_values: collection of floor total values and NFT collection names
    :type nft_values: list
    :return: list
    """
    nft_values = [
        (
            sum(
                nft.get("amount", 0)
                * float(nft.get("nft").get("floor")[0].get("price", 0))
                for nft in collection.get("nfts", [])
                if nft.get("nft", {}).get("floor")
            ),
            collection.get("name", ""),
        )
        for collection in serialized_data.get("nftcollections", [])
    ]
    return sorted(nft_values, reverse=True)


def _staked_totals_from_assets_data(assets_data):
    """Calculate and return collection of asset IDs and related staked values.

    :param assets_data: processed asset section data ready for rendering
    :type assets_data: dict
    :return: dict
    """
    return {
        asa.get("info").id: sum(
            elem.value
            for elem in asa.get("body", [])
            if elem.type == "Staked" and "farm" not in elem.name
        )
        for asa in assets_data.get("asa", [])
    }


def _staked_totals_from_serialized_data(serialized_data):
    """Calculate and return collection of asset IDs and related staked values.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :return: dict
    """
    return {
        asaitem.get("asset").get("id"): sum(
            float(program.get("value", 0))
            for program in asaitem.get("programs", [])
            if program.get("program").get("type") == "Staked"
            and "farm" not in program.get("program").get("name")
        )
        for asaitem in serialized_data.get("asaitems", [])
    }


def _total_from_serialized_data(serialized_data):
    """Return a :class:`utils.structs.Total` instance from serialized total dict.

    The serialized ``total`` carries decimal-string values; this helper casts
    them to floats so the resulting instance is compatible with the existing
    chart functions (notably :func:`_ratio_chart_data`, which divides by
    ``total.total`` and reads ``total.nft``).

    The API 2.0 serialized payload includes ``totalwonft`` / ``totalwonftusdc``
    fields not present on :class:`utils.structs.Total`; they're ignored here
    because no caller needs them.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :return: :class:`utils.structs.Total`
    """
    raw = serialized_data.get("total") or {}

    def _f(key):
        try:
            return float(raw.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    return Total(
        algo=_f("algo"),
        asa=_f("asa"),
        nft=_f("nft"),
        total=_f("total"),
        totalusdc=_f("totalusdc"),
        priceusdc=_f("priceusdc"),
        pricealgo=_f("pricealgo"),
        noteval=int(raw.get("noteval", 0) or 0),
    )


def _unit_for_asaitem(asaitem):
    """Return unit string for provided serialized asaitem.

    Mirrors the fallback used by :func:`_base_chart_data`:
    use the asset's unit if present, otherwise the asset id as a string,
    otherwise "ALGO".

    :param asaitem: serialized asaitem
    :type asaitem: dict
    :return: str
    """
    asset = asaitem.get("asset") or {}
    return asset.get("unit") or asset.get("id") or "ALGO"


# # PUBLIC
def prepare_base_charts(asas, values, nft_values):
    """Prepare and return data for ASA and NFT charts.

    :param asas: collection of assets immutable data
    :type asas: dict
    :param values: collection of amounts and data related to asset
    :type values: list
    :param nft_values: collection of amounts and data related to NFT
    :type nft_values: list
    :var asa_colors: collection of asset ids and related CSS color prefixes
    :type asa_colors: dict
    :var nft_colors: collection of NFT collections and related CSS color prefixes
    :type nft_colors: dict
    :return: tuple
    """
    asa_colors = {ALGO_ID: "algo"}
    nft_colors = {}
    return (
        _asa_chart(asas, values, asa_colors),
        _nft_chart(nft_values, nft_colors),
        asa_colors,
        nft_colors,
    )


def prepare_base_charts_from_assets_data(assets_data):
    """Prepare and return data for ASA and NFT charts.

    :param assets_data: processed asset section data ready for rendering
    :type assets_data: dict
    :var asa_colors: collection of asset ids and related CSS color prefixes
    :type asa_colors: dict
    :var nft_colors: collection of NFT collections and related CSS color prefixes
    :type nft_colors: dict
    :return: tuple
    """
    asa_colors = {ALGO_ID: "algo"}
    nft_colors = {}
    return (
        _asa_chart_from_assets_data(assets_data.get("asa", []), asa_colors),
        _nft_chart_from_assets_data(assets_data.get("nft", []), nft_colors),
        asa_colors,
        nft_colors,
    )


def prepare_consolidated_charts(serialized_data, asas, values, total, nft_colors):
    """Prepare and return charts for consolidated view.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param asas: collection of assets immutable data
    :type asas: dict
    :param values: collection of amounts and data related to asset
    :type values: list
    :param total: totals collection
    :type total: :class:`Total`
    :param nft_colors: collection of NFT collections and related CSS color prefixes
    :type nft_colors: dict
    :var consolidated_data: all the data needed for consolidated view
    :type consolidated_data: :class:`utils.structs.Consolidated`
    :var consolidated_totals: consolidated view totals
    :type consolidated_totals: :class:`utils.structs.Consolidated`
    :var distribution_chart: top assets distribution chart data
    :type distribution_chart: dict
    :var ratio_chart: ratio chart data
    :type ratio_chart: dict
    :var nftfloor_chart: NFT floor chart data
    :type nftfloor_chart: dict
    :return: tuple
    """
    consolidated_data = _consolidated_data_from_serialized_data(serialized_data)
    consolidated_totals = _consolidated_totals_from_consolidated_data(consolidated_data)

    distribution_chart = _distribution_chart(asas, values, consolidated_data)
    ratio_chart = _ratio_chart(total, consolidated_totals)
    nftfloor_chart = _nft_chart(consolidated_data.nftfloor, {}, label="NFT floor data")
    _assign_nftfloor_colors(nftfloor_chart, nft_colors)

    return (distribution_chart, ratio_chart, nftfloor_chart, consolidated_totals)


def prepare_consolidated_charts_from_assets_data(assets_data):
    """Prepare and return charts for consolidated view.

    :param assets_data: processed asset section data ready for rendering
    :type assets_data: dict
    :var consolidated_data: all the data needed for consolidated view
    :type consolidated_data: :class:`utils.structs.Consolidated`
    :var consolidated_totals: consolidated view totals
    :type consolidated_totals: :class:`utils.structs.Consolidated`
    :var distribution_chart: top assets distribution chart data
    :type distribution_chart: dict
    :var ratio_chart: ratio chart data
    :type ratio_chart: dict
    :return: tuple
    """
    consolidated_data = _consolidated_data_from_assets_data(assets_data)
    consolidated_totals = _consolidated_totals_from_consolidated_data(consolidated_data)

    distribution_chart = _distribution_chart_from_assets_data(
        assets_data, consolidated_data
    )
    ratio_chart = _ratio_chart(assets_data.get("total"), consolidated_totals)

    return (distribution_chart, ratio_chart, consolidated_totals)


def prepare_base_charts_from_serialized_data(serialized_data):
    """Prepare and return data for ASA and NFT charts from serialized account data.

    Counterpart of :func:`prepare_base_charts` that consumes API 2.0
    serialized data directly, with no dependence on legacy ``asas`` /
    ``values`` / ``nft_values`` shapes.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :var asa_colors: collection of asset ids and related CSS color prefixes
    :type asa_colors: dict
    :var nft_colors: collection of NFT collections and related CSS color prefixes
    :type nft_colors: dict
    :return: tuple
    """
    asa_colors = {ALGO_ID: "algo"}
    nft_colors = {}
    return (
        _asa_chart_from_serialized_data(serialized_data, asa_colors),
        _nft_chart_from_serialized_data(serialized_data, nft_colors),
        asa_colors,
        nft_colors,
    )


def prepare_consolidated_charts_from_serialized_data(serialized_data, nft_colors):
    """Prepare and return charts for the consolidated view from serialized data.

    Counterpart of :func:`prepare_consolidated_charts` that consumes API 2.0
    serialized data directly.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param nft_colors: collection of NFT collections and related CSS color prefixes
    :type nft_colors: dict
    :var consolidated_data: all the data needed for the consolidated view
    :type consolidated_data: :class:`utils.structs.Consolidated`
    :var consolidated_totals: consolidated view totals
    :type consolidated_totals: :class:`utils.structs.Consolidated`
    :var total: totals instance built from serialized data
    :type total: :class:`utils.structs.Total`
    :var distribution_chart: top assets distribution chart data
    :type distribution_chart: dict
    :var ratio_chart: ratio chart data
    :type ratio_chart: dict
    :var nftfloor_chart: NFT floor chart data
    :type nftfloor_chart: dict
    :return: tuple
    """
    consolidated_data = _consolidated_data_from_serialized_data(serialized_data)
    consolidated_totals = _consolidated_totals_from_consolidated_data(consolidated_data)
    total = _total_from_serialized_data(serialized_data)

    distribution_chart = _distribution_chart_from_serialized_data(
        serialized_data, consolidated_data
    )
    ratio_chart = _ratio_chart(total, consolidated_totals)
    nftfloor_chart = _nft_chart(consolidated_data.nftfloor, {}, label="NFT floor data")
    _assign_nftfloor_colors(nftfloor_chart, nft_colors)

    return (distribution_chart, ratio_chart, nftfloor_chart, consolidated_totals)
