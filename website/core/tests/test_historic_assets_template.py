"""The historic widget's rows must carry the colour of their chart slice.

This lives in the host suite, not the widget's, on purpose. The widget's own
tests run standalone -- `settings.configure()` with no TEMPLATES and the host
modules stubbed out -- which is what keeps it a separate package. Rendering its
templates through the real engine needs the host's settings and the host's
`core_extras` filters, so that is a host-side concern, and it is the host that
renders these templates in production anyway.

What is checked: the stripe down the left of a row is the only thing tying it
to its share of the pie chart above. `charts.py` builds the slot maps and the
consumer spreads them into the context, but the template never looked them up,
so every row fell back to the grey reserved for the "others" slice while the
chart beside it was in full colour. Nothing failed; the page was just uniformly
grey where it should have been legible.
"""

from django.template.loader import render_to_string

#: `asa_batch` skips any item with an empty body, so rows need one.
PROGRAM = {"type": "Balance", "amount": "5", "name": "", "url": "", "source": [""]}


def _asa_item(asset_id, label):
    return {
        "info": {"id": asset_id, "name": label, "unit": label},
        "header": {"amount": "5", "label": label, "icon": "icon.png", "total": "12.5"},
        "body": [PROGRAM],
    }


def _collection(name):
    return {
        "info": name,
        "header": {"amount": "2", "label": name, "total": "9"},
        "body": [],
    }


def _render(partial, **context):
    return render_to_string(
        f"historic/assets.html#{partial}",
        {"base_cdn_url": "https://cdn.example", **context},
    )


class TestHistoricAssetsColours:
    """Testing class for colour slots on the widget's streamed rows."""

    def test_historic_assets_charted_asset_carries_its_slot(self):
        html = _render(
            "asa_batch", items=[_asa_item(31566704, "USDC")], colors={31566704: "3"}
        )

        assert 'class="item-header token c3"' in html

    def test_historic_assets_uncharted_asset_falls_back(self):
        """No slot means the asset sits inside the "others" slice.

        The stylesheet's default stripe is that slice's grey, so the absence of
        a class is correct. An empty `c` would not be.
        """
        html = _render("asa_batch", items=[_asa_item(999, "Unlisted")], colors={})

        assert 'class="item-header token"' in html
        assert ' c"' not in html

    def test_historic_assets_rows_differ_when_the_chart_does(self):
        """The point of the slot: two rows, two colours."""
        html = _render(
            "asa_batch",
            items=[_asa_item(1, "AAA"), _asa_item(2, "BBB")],
            colors={1: "0", 2: "7"},
        )

        assert "item-header token c0" in html
        assert "item-header token c7" in html

    def test_historic_assets_collection_carries_its_slot(self):
        html = _render("nft_batch", items=[_collection("Fugu")], nft_colors={"Fugu": "5"})

        assert "item-header nft c5" in html

    def test_historic_assets_collection_without_a_slot_falls_back(self):
        html = _render("nft_batch", items=[_collection("Fugu")], nft_colors={})

        assert 'class="item-header nft"' in html

    def test_historic_assets_survives_a_missing_slot_map(self):
        """A batch can render before the maps exist; it must not raise.

        The consumer streams the scaffold and each batch as separate messages,
        so a template that assumed a complete context would take the socket
        down rather than render a grey row.
        """
        html = _render("asa_batch", items=[_asa_item(1, "AAA")])

        assert "item-header token" in html
