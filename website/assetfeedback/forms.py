"""Module containing the asset feedback form."""

from algosdk.encoding import is_valid_address
from captcha.fields import CaptchaField
from django import forms
from django.core.validators import URLValidator

from assetfeedback.models import AssetFeedback

MAX_DETAILS = 1000
MAX_CONTACT = 200
FIELD_CLASS = "input input-sm w-full"


class AssetFeedbackForm(forms.Form):
    """Report about an asset; `show_personal` and `require_captcha` remove fields."""

    kind = forms.ChoiceField(
        label="What can you tell us?",
        choices=AssetFeedback.Kind.choices,
        widget=forms.Select(attrs={"class": "select select-sm w-full"}),
    )
    link = forms.URLField(
        label="Link (market, pool or announcement)",
        required=False,
        max_length=500,
        assume_scheme="https",
        validators=[URLValidator(schemes=["http", "https"])],
        widget=forms.URLInput(attrs={"class": FIELD_CLASS}),
    )
    details = forms.CharField(
        label="Details",
        required=False,
        max_length=MAX_DETAILS,
        widget=forms.Textarea(attrs={"class": "textarea w-full", "rows": 3}),
    )
    contact = forms.CharField(
        label="Contact (Discord, X or email, optional)",
        required=False,
        max_length=MAX_CONTACT,
        widget=forms.TextInput(attrs={"class": FIELD_CLASS}),
    )
    reporter_address = forms.CharField(
        label="Your Algorand address (optional)",
        required=False,
        max_length=58,
        widget=forms.TextInput(attrs={"class": FIELD_CLASS}),
    )
    # Honeypot: the view reads this name, and a real browser leaves it empty.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )
    started = forms.CharField(widget=forms.HiddenInput)
    captcha = CaptchaField()

    def __init__(self, *args, show_personal=True, require_captcha=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not show_personal:
            del self.fields["contact"]
            del self.fields["reporter_address"]
        if not require_captcha:
            del self.fields["captcha"]

    def clean_reporter_address(self):
        """Return the address after checking that it is a valid Algorand one.

        :return: str
        """
        address = self.cleaned_data["reporter_address"].strip()
        if address and not is_valid_address(address):
            raise forms.ValidationError("Enter a valid Algorand address.")
        return address

    def clean(self):
        """Require details or a link.

        :return: dict
        """
        cleaned = super().clean()
        if not self.errors and not (cleaned.get("details") or cleaned.get("link")):
            self.add_error("details", "Add some details or a link.")
        return cleaned
