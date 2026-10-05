"""Render both NFT item snippets and check where their market links point."""

import pytest
from django.template.loader import render_to_string

TEMPLATES = ("snippets/nfts/item.html", "snippets/dynamic/nft.html")
GROUP = "iFF1fhiS3v+ZLwpDtF/E18N3evm4H3OlLUw9U0mgMF4="


def _row():
    purchase = {
        "price": "42.000000",
        "market": {"name": "ALGOxNFT"},
        "link": f"group={GROUP}",
        "epoch": 1646937642,
        "currency": None,
    }
    return {
        "amount": 1,
        "price": "48.340000",
        "value": "48.340000",
        "nft": {
            "id": 492076550,
            "name": "AB2 item",
            "unit": "AB2",
            "total": 1,
            "image": "/thumbnails/x.png",
            "urls": [],
            "listings": [
                {
                    "price": "25.000000",
                    "market": {"name": "AB2 Gallery"},
                    "link": "application=678788407",
                    "currency": None,
                },
                {
                    "price": "49.500000",
                    "market": {"name": "EXA Market"},
                    "link": "https://exa.market/asset/492076550",
                    "currency": None,
                },
            ],
            "floor": [],
            "last_purchase": {**purchase, "price": "1.000000"},
            "max_purchase": purchase,
            "traits": [],
        },
    }


@pytest.mark.parametrize("template", TEMPLATES)
def test_nft_item_escrow_listing_links_to_application(template):
    html = render_to_string(template, {"row": _row()})
    assert 'href="https://allo.info/application/678788407"' in html
    assert 'href="https://exa.market/asset/492076550"' in html
    assert "application=678788407" not in html


@pytest.mark.parametrize("template", TEMPLATES)
def test_nft_item_escrow_listing_is_labelled_escrowed(template):
    html = render_to_string(template, {"row": _row()}).lower()
    assert "escrowed by" in html or "escrowed</span>" in html


@pytest.mark.parametrize("template", TEMPLATES)
def test_nft_item_purchase_links_to_encoded_group(template):
    html = render_to_string(template, {"row": _row()})
    assert (
        'href="https://allo.info/tx/group/'
        'iFF1fhiS3v%2BZLwpDtF%2FE18N3evm4H3OlLUw9U0mgMF4%3D"'
    ) in html
    assert "Show purchase in Allo" not in html


def test_dynamic_nft_escrowed_listing_is_not_called_an_ask():
    html = render_to_string("snippets/dynamic/nft.html", {"row": _row()})
    assert html.count('<small class="qualifier">escrowed at</small>') == 1
    assert html.count('<small class="qualifier">asking</small>') == 1


def test_dynamic_nft_listing_chip_keeps_its_space_through_minification():
    from core.middleware import CustomMinifyHtmlMiddleware
    import minify_html

    html = minify_html.minify(
        render_to_string("snippets/dynamic/nft.html", {"row": _row()}),
        **CustomMinifyHtmlMiddleware.minify_args,
    )
    assert "escrowed</span>\xa0<a" in html
    assert "listed</span>\xa0<a" in html
