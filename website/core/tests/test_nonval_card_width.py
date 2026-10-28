"""Not-evaluated cards shrink to their grid column. See logbook: snippets/nonval.html `min-w-0`."""

import re

from django.template.loader import render_to_string

LONG_URL = "ipfs://bafybeicrvwrfu223y5gixlfppmyvwgsfwo4ysdzwb6kqvhbosigba6vybu"


def _cards(html):
    return re.findall(r'<div id="\d+" class="([^"]*\bfitem\b[^"]*)"', html)


def test_a_not_evaluated_card_can_shrink_below_its_long_url():
    asset = {
        "id": 3754707863,
        "name": "Shrimp Ice Cream",
        "unit": "LOOT",
        "total": 1,
        "decimals": 0,
        "url": LONG_URL,
    }
    html = render_to_string(
        "snippets/nonval.html",
        {"notevals": [{"asset": asset, "amount": 1, "programs": []}]},
    )
    classes = _cards(html)
    assert classes
    assert all("min-w-0" in card.split() for card in classes)
    assert LONG_URL in html
