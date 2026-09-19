"""A holding whose asset metadata the engine could not resolve.

**A filter argument is not forgiving, and that is the whole bug here.** Django
swallows a failed lookup in ``{{ a.b }}`` and renders ``string_if_invalid``; it
does not swallow one in a filter's *argument*, because
``FilterExpression.resolve`` calls ``arg.resolve(context)`` directly. So
``{{ x|amount_repr:asset.decimals }}`` on a null ``asset`` raises
``VariableDoesNotExist`` and takes the whole address page down with a 500.

Seen in production on 2026-09-18 against ``BNFIREKG…``. A *not evaluated* asset
is exactly the one whose metadata could not be resolved, so a null asset there
is the ordinary case rather than an exotic one.

These render the fragments directly rather than a whole page: the question is
what one template does with one null, and a page render would drown that in
context-building.
"""

from django.template.loader import render_to_string


class TestANotEvaluatedAssetWithoutMetadata:
    def _noteval(self, asset):
        return {"notevals": [{"asset": asset, "amount": 12345678, "programs": []}]}

    def test_it_renders_rather_than_raising(self):
        """The page must survive. Before the guard this raised
        `VariableDoesNotExist` out of the template and became a 500."""
        html = render_to_string("snippets/nonval.html", self._noteval(None))

        assert "not evaluated" in html

    def test_the_amount_is_still_shown_in_base_units(self):
        """Without decimals the raw amount is what is true, and a card that
        says nothing is worse than one that says what it knows."""
        html = render_to_string("snippets/nonval.html", self._noteval(None))

        assert "12345678" in html
        assert "base units" in html

    def test_an_asset_with_metadata_is_scaled_as_before(self):
        """The guard must not cost the ordinary case its decimals.

        `12.3457`, not `12.345678`: `amount_repr` caps display at
        `MAX_AMOUNT_DECIMALS`, which is four.
        """
        asset = {"id": 31566704, "name": "USDC", "unit": "USDC", "decimals": 6}

        html = render_to_string("snippets/nonval.html", self._noteval(asset))

        assert "12.3457" in html
        assert "base units" not in html


class TestAProgramPanelWithoutAssetMetadata:
    """`snippets/asas/program.html` had the same shape in seven places."""

    def _context(self, asset):
        return {
            "asset": asset,
            "prog": {"amount": 500, "value": 1.0, "program": {"type": "Balance"}},
            "program": {"type": "Balance", "name": "Wallet balance"},
        }

    def test_it_renders_rather_than_raising(self):
        html = render_to_string("snippets/asas/program.html", self._context(None))

        assert html is not None

    def test_it_renders_with_metadata_too(self):
        """The `{% with %}` binding must not cost the ordinary case anything.

        Asserted as "renders" rather than on a figure: this panel's branches
        need `url_value`, `bundle` and a distribution to show one, and building
        that here would be testing the fixture rather than the guard. The
        figures are covered by the address-page suites.
        """
        asset = {"id": 31566704, "name": "USDC", "unit": "USDC", "decimals": 6}

        html = render_to_string("snippets/asas/program.html", self._context(asset))

        assert html is not None
