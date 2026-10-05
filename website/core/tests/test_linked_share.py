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


def _classic_raw(prog, asset=ASSET):
    return render_to_string(
        "snippets/asas/program.html",
        {"asset": asset, "prog": prog, "decimals": asset["decimals"]},
    )


def _dynamic_raw(prog, asset=ASSET):
    return render_to_string(
        "snippets/dynamic/position.html",
        {"asset": asset, "prog": prog, "counter": "1-1"},
    )


def _classic(prog, asset=ASSET):
    return _text(_classic_raw(prog, asset))


def _dynamic(prog, asset=ASSET):
    return _text(_dynamic_raw(prog, asset))


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

    def test_application_marker_becomes_an_explorer_link(self):
        cdp = {
            "text": "CompX CDP",
            "link": "application=2965407870",
            "amount": 2500000,
            "share": "40.00",
        }
        for html in (_classic_raw(_prog(cdp)), _dynamic_raw(_prog(cdp))):
            assert 'href="application=' not in html
            assert re.search(r'href="https://[^"]+2965407870[^"]*"', html)
            assert "CompX CDP 40.00% (2.5000 USDC)" in _text(html)

    def test_plain_link_is_kept(self):
        for html in (_classic_raw(_prog(FARM)), _dynamic_raw(_prog(FARM))):
            assert 'href="https://www.alphaarcade.com/stake"' in html
