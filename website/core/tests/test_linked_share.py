"""Testing how both layouts show the share of a source token held by a platform."""

import re
from html import unescape

from django.template.loader import render_to_string

ASSET = {"id": 31566704, "name": "USDC", "unit": "USDC", "decimals": 6}

FARM = {
    "text": "Alpha Arcade stake",
    "link": "https://www.alphaarcade.com/stake",
    "amount": 107825,
    "share": "91.44",
}

SOURCE = {
    "text": "Source LP token",
    "amount": 1202961,
    "balance": 102961,
    "id": 2741116468,
}


def _prog(*linked):
    return {
        "amount": 117918,
        "value": "0.929091",
        "pid": "p1-31566704-4432d35d431a95dc",
        "pid_ambiguous": False,
        "program": {
            "type": "Added",
            "name": "Liquidity",
            "provider": {"name": "Tinyman2 LP"},
            "url": "https://app.tinyman.org/#/pool/J7CN",
            "code": "Tinyman2 LP USDC-ALPHA",
        },
        "linked": list(linked),
    }


def _text(html):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", html)))


def _classic(prog, asset=ASSET):
    return _text(
        render_to_string(
            "snippets/asas/program.html",
            {"asset": asset, "prog": prog, "decimals": asset["decimals"]},
        )
    )


def _dynamic(prog, asset=ASSET):
    return _text(
        render_to_string(
            "snippets/dynamic/position.html",
            {"asset": asset, "prog": prog, "counter": "1-1"},
        )
    )


class TestLinkedShare:
    def test_classic_shows_share_and_side_amount(self):
        assert "Alpha Arcade stake 91.44% (0.1078 USDC)" in _classic(_prog(SOURCE, FARM))

    def test_dynamic_shows_share_and_side_amount(self):
        assert "Alpha Arcade stake 91.44% (0.1078 USDC)" in _dynamic(_prog(SOURCE, FARM))

    def test_tiny_share_is_not_shown_as_zero(self):
        farm = {**FARM, "share": "0.00", "amount": None}
        html = _dynamic(_prog(farm))
        assert "Alpha Arcade stake <0.01%" in html
        assert "0.00%" not in html

    def test_no_share_keeps_the_bare_link(self):
        farm = {"text": FARM["text"], "link": FARM["link"]}
        for html in (_classic(_prog(SOURCE, farm)), _dynamic(_prog(SOURCE, farm))):
            assert "Alpha Arcade stake" in html
            assert "%" not in html

    def test_dynamic_ignores_amount_without_share(self):
        """The consensus "Expiry" entry carries an amount that is not a holding."""
        expiry = {"text": "Expiry", "amount": 51234567, "info": "in 10 days"}
        assert "51.234567" not in _dynamic(_prog(expiry))
