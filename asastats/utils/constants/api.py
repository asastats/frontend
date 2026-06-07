"""Module containing API constants."""

from utils.constants.core import ASASTATS_SLOGANS

API_ENTRY_VALUE_CODE = "value"
API_ENTRY_LINKS_CODE = "links"
API_ENTRY_AMOUNT_CODE = "amount"
API_ENTRY_PRICE_CODE = "price"

API_ENTRY_TYPES = {
    API_ENTRY_VALUE_CODE: (
        "linktext",
        "link",
        "title",
        "text",
        "border",
        "value",
        "bracket",
    ),
    API_ENTRY_AMOUNT_CODE: ("text", "amount", "unit", "border", "bracket"),
    API_ENTRY_LINKS_CODE: ("small", "linktext", "link", "title"),
    API_ENTRY_PRICE_CODE: ("price", "unit"),
}

API_RESPONSE_OBJECTS = (
    "addresses",
    "total",
    "values",
    "nft_values",
    "noteval",
    "ratiochart",
    "asachart",
    "nftchart",
    "colors",
    "nft_colors",
)

API_GLOBAL_SETTINGS = {
    "asa_colors": {
        "0": "#e6194B",
        "1": "#3cb44b",
        "2": "#ffe119",
        "3": "#4363d8",
        "4": "#f58231",
        "5": "#42d4f4",
        "6": "#f032e6",
        "7": "#fabed4",
        "8": "#469990",
        "9": "#dcbeff",
        "10": "#9A6324",
        "11": "#fffac8",
        "12": "#800000",
        "13": "#aaffc3",
        "14": "#000075",
        "15": "#a9a9a9",
        "16": "#ffffff",
        "17": "#000000",
    },
    "nft_colors": {
        "0": "#500000",
        "1": "#003300",
        "2": "#6e5e00",
        "3": "#000052",
        "4": "#610000",
        "5": "#00506d",
        "6": "#5b005e",
        "7": "#703e52",
        "8": "#00221b",
        "9": "#573f76",
        "10": "#2a0000",
        "11": "#767347",
        "12": "#280000",
        "13": "#1e7543",
        "14": "#00000a",
        "15": "#2f2f2f",
        "16": "#777777",
        "17": "#000000",
    },
    "providers": {"path": "static/icons/providers/"},
    "slogans": ASASTATS_SLOGANS,
}
