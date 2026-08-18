"""The tax-export form's hints have to reach the reader.

Every hint on this form was a Materialize tooltip: `.tooltipped` with
`data-tooltip`, constructed by `$.fn.tooltip()`. That plugin left with the
framework, so `tax.js` guarded the call -- correctly, since an unguarded throw
there runs inside jQuery's ready queue and would abandon the three bindings
declared after it. What the guard could not do was render the hints, so three
pieces of text went missing from the page and stayed missing:

* "Not implemented yet", on every provider but Koinly -- so the others looked
  selectable and simply did not work;
* `ExportForm.use_mve.help_text` and `.non_zero.help_text`, both defined in
  `core/forms.py` and shown nowhere.

Nothing failed. The form submitted, the tests passed, and the help text existed
only in the source.
"""

import pytest
from django.template.loader import render_to_string

from core.forms import ExportForm


@pytest.fixture
def rendered():
    return render_to_string("snippets/taxprepare.html", {"form": ExportForm()})


class TestCoreTaxprepareTemplate:
    """Testing class for the tax-export form's hints and hooks."""

    def test_core_taxprepare_help_text_is_rendered(self, rendered):
        """Not only carried in an attribute: written where it can be read.

        A hint a reader has to hover to discover is one most readers never
        discover, and on a touch screen there is no hover at all.
        """
        form = ExportForm()

        for field in ("use_mve", "non_zero"):
            help_text = form[field].help_text
            assert help_text, f"{field} has no help text to render"
            assert help_text in rendered, f"{field}'s help text is not on the page"

    def test_core_taxprepare_unimplemented_providers_say_so(self, rendered):
        assert "Not implemented yet" in rendered

    def test_core_taxprepare_uses_the_attribute_the_styling_reads(self, rendered):
        """`data-tip` is DaisyUI's; `data-tooltip` was Materialize's.

        The class was carried over but the attribute was not renamed, so the
        tooltip had a value that nothing displayed.
        """
        assert "data-tip=" in rendered
        assert "data-tooltip" not in rendered
        assert "tooltipped" not in rendered

    def test_core_taxprepare_keeps_its_script_hooks(self, rendered):
        """`tax.js` binds submit on the form and disables the button."""
        assert 'id="process_form"' in rendered
        assert 'id="process"' in rendered

    def test_core_taxprepare_offers_every_provider(self, rendered):
        for _, label in ExportForm().fields["provider"].choices:
            assert label in rendered, f"{label} is missing from the form"
