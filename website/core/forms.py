"""Module containing code dealing with core app's forms."""

from algosdk.constants import ADDRESS_LEN
from captcha.fields import CaptchaField
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import (
    BaseInlineFormSet,
    BooleanField,
    CharField,
    CheckboxInput,
    ChoiceField,
    Form,
    RadioSelect,
    Select,
    Textarea,
)
from django.forms.models import ModelForm, inlineformset_factory
from django.forms.widgets import TextInput

from core.helpers import addresses_from_raw, format_addresses_limit_help_text
from core.models import BundleName, Profile
from utils.constants.core import INVALID_ADDRESS_TEXT, MAX_BUNDLE_SIZE
from utils.constants.explorers import explorer_choices
from utils.constants.tax import (
    TAX_FORM_NON_ZERO_HELP_TEXT,
    TAX_FORM_PROVIDERS,
    TAX_FORM_USE_MVE_HELP_TEXT,
)
from utils.constants.users import (
    BUNDLENAME_PUBLIC_HELP_TEXT,
    REQUIRED_BUNDLE_ADDRESSES_ERROR,
    REQUIRED_BUNDLE_NAME_ERROR,
    TOO_LONG_BUNDLE_ADDRESSES_ERROR,
    TOO_LONG_BUNDLE_NAME_ERROR,
    TOO_LONG_USER_FIRST_NAME_ERROR,
    TOO_LONG_USER_LAST_NAME_ERROR,
)
from utils.helpers import check_algorand_address
from utils.userhelpers import validate_address_or_algo_name_url_path
from widgethost.registry import swap_routers


# # CORE
class AddressForm(Form):
    """Form class for entering Algorand address(es) and/or ANS/NFD name(s).

    :var AddressForm.address: field holding Algorand address or ANS/NFD name
    :type AddressForm.address: :class:`.CharField`
    :var AddressForm.bundle: field holding multiple Algorand addresses or ANS/NFD names
    :type AddressForm.bundle: :class:`.CharField`
    """

    address = CharField(required=False, max_length=ADDRESS_LEN)
    bundle = CharField(required=False, max_length=MAX_BUNDLE_SIZE * (ADDRESS_LEN + 5))

    def clean(self):
        """Raise ValidationError if address field isn't a valid Algorand address.

        Return address or multiple addresses separated by spaces.

        :var data: multiple entries data from bundle field
        :type data: str
        :var address_data: data from address field
        :type address_data: str
        :var bundle: parsed collection of addresses
        :type bundle: list
        :return: str
        """
        data = self.cleaned_data.get("bundle")
        address_data = self.cleaned_data.get("address")
        return addresses_from_raw(data, address_data=address_data)


class ExportDownloadForm(Form):
    """Form class for downloading compressed file with CSV file(s) inside.

    :var ExportDownloadForm.agree: field user needs to check to proceeed
    :type ExportDownloadForm.agree: :class:`.BooleanField`
    """

    agree = BooleanField(required=True)


class ExportForm(Form):
    """Form class for entering arguments for CSV files processing.

    :var ExportForm.provider: field holding tax software provider
    :type ExportForm.provider: :class:`.ChoiceField`
    :var ExportForm.use_mve: field indicating use of maximum value engine
    :type ExportForm.use_mve: :class:`.BooleanField`
    :var ExportForm.non_zero: field indicating adding additional non-tero values CSV file
    :type ExportForm.non_zero: :class:`.BooleanField`
    """

    provider = ChoiceField(
        widget=RadioSelect(attrs={"class": "with-gap"}),
        choices=TAX_FORM_PROVIDERS,
        initial="koinly",
    )
    use_mve = BooleanField(
        required=False,
        label="Use maximum value engine",
        help_text=TAX_FORM_USE_MVE_HELP_TEXT,
    )
    non_zero = BooleanField(
        required=False,
        label="Include CSV file with non-zero values",
        help_text=TAX_FORM_NON_ZERO_HELP_TEXT,
    )

    def clean(self):
        """Raise ValidationError if provider isn't Koinly.

        :var provider: provider field's value
        :type provider: str
        """
        cleaned_data = super().clean()
        provider = self.cleaned_data.get("provider")
        if provider != "koinly":
            raise ValidationError("Only Koinly is available as provider for now.")

        return cleaned_data


# # USERS
class CustomSignupForm(Form):
    """Subclass of :class`Form` with overridden `Form.signup` method."""

    def signup(self, request, user):
        """Dummy overridden `Form.signup` method as required by django-allauth."""


class BaseBundleNameForm(ModelForm):
    """Base model form class for creating and editing bundle names.

    :var name: field holding bundle's name
    :type name: :class:`CharField`
    :var addresses: field holding bundle's addresses
    :type addresses: :class:`CharField`
    :var public: field indicating if bundle's name is publicly available
    :type public: :class:`.BooleanField`
    """

    name = CharField(
        required=True,
        widget=TextInput(attrs={"autofocus": "autofocus", "length": "50"}),
    )
    addresses = CharField(
        required=True,
        widget=Textarea(
            attrs={
                "class": "materialize-textarea",
                "rows": 20,
                "placeholder": "Enter Algorand addresses and/or .algo names",
            }
        ),
    )
    public = BooleanField(
        required=False,
        widget=CheckboxInput(),
        label="Public URL",
        help_text=BUNDLENAME_PUBLIC_HELP_TEXT,
    )

    class Meta:
        model = BundleName
        fields = ("name", "addresses", "public")
        error_messages = {
            "name": {
                "required": REQUIRED_BUNDLE_NAME_ERROR,
                "max_length": TOO_LONG_BUNDLE_NAME_ERROR,
            },
            "addresses": {
                "required": REQUIRED_BUNDLE_ADDRESSES_ERROR,
                "max_length": TOO_LONG_BUNDLE_ADDRESSES_ERROR,
            },
        }

    def clean(self):
        """Raise ValidationError if addresses field doesn't contain valid addresses

        or if integrity checks have failed.

        :return: dict
        """
        super().clean()
        self.cleaned_data["addresses"] = addresses_from_raw(
            self.cleaned_data["addresses"],
            max_bundle_size=self.instance.profile.bundle_size_limit(self.instance),
        )
        if self.cleaned_data.get("name"):
            validate_address_or_algo_name_url_path(self.cleaned_data.get("name"))
            self.instance.profile.bundlename_system_reserved_url_path_check(
                self.cleaned_data.get("name")
            )
            self.instance.profile.integrity_check_for_bundlename(
                self.instance.id, self.cleaned_data
            )
            if self.cleaned_data.get("public"):
                self.instance.profile.integrity_check_for_public_bundlename(
                    self.instance.id, self.cleaned_data
                )

        return self.cleaned_data


class ProfileBundleNameForm(BaseBundleNameForm):
    """Form class for creating and editing bundle names."""

    def __init__(self, for_profile, *args, **kwargs):
        """Set ProfileBundleNameForm.instance.profile to provided `for_profile`.

        Prior to that, call BaseBundleNameForm dunder init method with provided
        positional and named arguments.
        """
        super().__init__(*args, **kwargs)
        self.instance.profile = for_profile
        self.fields["addresses"].help_text = format_addresses_limit_help_text(
            self.instance
        )


class DeactivateProfileForm(Form):
    """Form class for deactivating current user.

    Only requirement is to correctly populate captcha field.
    User object is taken from the request object.

    :var captcha: field holding value that is going to be compared with captcha
    :type captcha: :class:`CaptchaField`
    """

    captcha = CaptchaField()

    def deactivate_profile(self, request):
        """Logout and deactivate given request's user in database.

        :param request: http request
        :type request: :class:`HttpRequest`
        """
        request.user.is_active = False
        request.user.save()
        logout(request)


class UpdateUserForm(ModelForm):
    """Model form class for editing user's data."""

    class Meta:
        model = User
        fields = ("first_name", "last_name")
        labels = {
            "first_name": "First name",
            "last_name": "Last name",
        }
        error_messages = {
            "first_name": {
                "max_length": TOO_LONG_USER_FIRST_NAME_ERROR,
            },
            "last_name": {
                "max_length": TOO_LONG_USER_LAST_NAME_ERROR,
            },
        }


class ProfileInlineForm(BaseInlineFormSet):
    """Form class for editing user profile's data.

    :var permission: user's permission on website
    :type permission: int
    """

    address = CharField(required=False, max_length=ADDRESS_LEN)

    class Meta:
        model = Profile
        fields = ["address"]

    def clean(self):
        """Validate if address field contains a valid public Algorand address.

        :return: list
        """
        if self.cleaned_data[0]["address"]:
            address = check_algorand_address(self.cleaned_data[0]["address"])
            if not address:
                self.forms[0].add_error("address", INVALID_ADDRESS_TEXT)
                raise ValidationError(INVALID_ADDRESS_TEXT)

        return self.cleaned_data


ProfileFormSet = inlineformset_factory(
    User,
    Profile,
    formset=ProfileInlineForm,
    fields=("address",),
)
"""Formset for editing profile's data.
It is instantiated together with :class:`UpdateUserForm` form instance
in the common user/profile editing process.
"""


class ProfileRouterForm(ModelForm):
    """Form for choosing the profile's preferred smart router.

    Router choices are discovered (manifests with ``category = "swap"``), so a
    newly added router widget appears here with no change to this form.
    """

    class Meta:
        model = Profile
        fields = ("preferred_router",)

    def __init__(self, *args, **kwargs):
        """Populate the router select from discovered swap-category widgets."""
        super().__init__(*args, **kwargs)
        self.fields["preferred_router"] = ChoiceField(
            choices=swap_routers(),
            required=True,
            label="Smart router",
            widget=Select(attrs={"class": "browser-default"}),
        )


class ProfileExplorerForm(ModelForm):
    """Form for choosing the profile's preferred blockchain explorer.

    Explorer choices come from the explorer registry (Allo first), so adding a
    provider there surfaces it here with no change to this form. The right to
    submit this form is gated on the Intro tier; the view enforces that and the
    template renders the control disabled (routing a click to subscriptions) for
    users below it.
    """

    class Meta:
        model = Profile
        fields = ("preferred_explorer",)

    def __init__(self, *args, **kwargs):
        """Populate the explorer select from the explorer registry."""
        super().__init__(*args, **kwargs)
        self.fields["preferred_explorer"] = ChoiceField(
            choices=explorer_choices(),
            required=True,
            label="Explorer",
            widget=Select(attrs={"class": "browser-default"}),
        )
