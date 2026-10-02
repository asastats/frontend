"""Testing the ids the classic layout gives position values."""

from django.template.loader import render_to_string

ASSET = {"id": 393537671, "name": "ASA Stats", "unit": "ASASTATS", "decimals": 6}


def _render(ambiguous):
    return render_to_string(
        "snippets/asas/program.html",
        {
            "asset": ASSET,
            "prog": {
                "amount": 500,
                "value": 0.84,
                "pid": "p1-393537671-62fc210536a07b93",
                "pid_ambiguous": ambiguous,
                "program": {"type": "Staked", "name": "Cometa stake"},
            },
        },
    )


class TestClassicPositionValueIds:
    def test_a_named_position_carries_the_id_its_fragment_swaps_on(self):
        html = _render(False)

        assert 'id="ppv-p1-393537671-62fc210536a07b93"' in html

    def test_an_ambiguous_position_has_no_id(self):
        """Two Cometa stakes share one pid; the engine sends neither, and a
        duplicate id is invalid DOM. The dynamic layout already skips these."""
        html = _render(True)

        assert 'id="ppv-' not in html
        assert 'data-cat="staked"' in html
