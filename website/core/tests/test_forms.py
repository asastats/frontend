"""Testing module for :py:mod:`website.core.forms` module."""

import time

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import (
    BaseInlineFormSet,
    BooleanField,
    CharField,
    CheckboxInput,
    ChoiceField,
    Form,
    ModelForm,
    RadioSelect,
    Textarea,
)
from django.forms.widgets import TextInput

from core.forms import (
    ADDRESS_LEN,
    AddressForm,
    BaseBundleNameForm,
    CaptchaField,
    CustomSignupForm,
    DeactivateProfileForm,
    ExportDownloadForm,
    ExportForm,
    ProfileBundleNameForm,
    ProfileExplorerForm,
    ProfileFormSet,
    ProfileInlineForm,
    ProfileRouterForm,
    UpdateUserForm,
)
from core.models import BundleName, Profile
from utils.constants.core import INVALID_ADDRESS_TEXT, MAX_BUNDLE_SIZE
from utils.constants.tax import (
    TAX_FORM_NON_ZERO_HELP_TEXT,
    TAX_FORM_PROVIDERS,
    TAX_FORM_USE_MVE_HELP_TEXT,
)
from utils.constants.users import (
    BUNDLENAME_PUBLIC_HELP_TEXT,
    TOO_LONG_USER_FIRST_NAME_ERROR,
    TOO_LONG_USER_LAST_NAME_ERROR,
)
from utils.tests.fixtures import TEST_ADDRESS, TEST_ADDRESS2


# # CORE
class TestAddressForm:
    """Testing class for :class:`AddressForm`."""

    # # AddressForm
    def test_addressform_issubclass_of_form(self):
        assert issubclass(AddressForm, Form)

    def test_addressform_has_address_field(self):
        form = AddressForm()
        assert form.fields.get("address") is not None
        assert isinstance(form.fields["address"], CharField)
        assert form.fields["address"].max_length == ADDRESS_LEN

    def test_addressform_has_bundle_field(self):
        form = AddressForm()
        assert form.fields.get("bundle") is not None
        assert isinstance(form.fields["bundle"], CharField)
        assert form.fields["bundle"].max_length == MAX_BUNDLE_SIZE * (ADDRESS_LEN + 5)

    # # clean
    @pytest.mark.parametrize(
        "address",
        [
            "",
            None,
            0,
            "foobar",
            "VKENBO5W2DZAZFQR45SOQO6IMWS5UMVZCHLPEACNOII7BDJTGBZKSEL4Y",
            "393537671",
            "#17180006",
        ],
    )
    def test_addressform_is_not_valid_for_invalid_address(self, address):
        form = AddressForm(data={"address": address})
        assert not form.is_valid()
        assert form.errors["__all__"][0] == INVALID_ADDRESS_TEXT

    def test_addressform_is_valid_for_valid_address(self):
        form = AddressForm(data={"address": TEST_ADDRESS})
        assert form.is_valid()

    @pytest.mark.parametrize(
        "bundle",
        [
            "    ",
            None,
            0,
            "foobar foobar foobar foobar",
            "VKENBO5W2DZAZFQR45SOQO6IMWS5UMVZCHLPEACNOII7BDJTGBZKSEL4Y",
            "393537671 393537671",
            "#17180006 #17180006",
        ],
    )
    def test_addressform_is_not_valid_for_invalid_bundle(self, bundle):
        form = AddressForm(data={"bundle": bundle})
        assert not form.is_valid()
        assert form.errors["__all__"][0] == INVALID_ADDRESS_TEXT

    def test_addressform_is_valid_for_valid_bundle(self):
        form = AddressForm(data={"bundle": f"{TEST_ADDRESS},{TEST_ADDRESS2}"})
        assert form.is_valid()

    def test_addressform_is_valid_for_valid_bundle_of_names(self, mocker):
        addresses1, addresses2 = "addresses1", "addresses2"
        mocker.patch(
            "core.forms.addresses_from_raw",
            return_value=f"{addresses1} {TEST_ADDRESS} {addresses2} {TEST_ADDRESS2}",
        )
        form = AddressForm(
            data={"bundle": f"name1.algo,{TEST_ADDRESS},name2.algo,{TEST_ADDRESS2}"}
        )
        assert form.is_valid()


class TestExportDownloadForm:
    """Testing class for :class:`ExportDownloadForm`."""

    # # ExportDownloadForm
    def test_exportdownloadform_issubclass_of_form(self):
        assert issubclass(ExportDownloadForm, Form)

    def test_exportdownloadform_has_agree_field_as_booleanfield(self):
        form = ExportDownloadForm()
        assert form.fields.get("agree") is not None
        assert isinstance(form.fields["agree"], BooleanField)

    def test_exportdownloadform_agree_field_sets_required_true(self):
        form = ExportDownloadForm()
        assert form.fields["agree"].required is True


class TestExportForm:
    """Testing class for :class:`ExportForm`."""

    # # ExportForm
    def test_exportform_issubclass_of_form(self):
        assert issubclass(ExportForm, Form)

    def test_exportform_has_provider_field_as_choicefield(self):
        form = ExportForm()
        assert form.fields.get("provider") is not None
        assert isinstance(form.fields["provider"], ChoiceField)

    def test_exportform_provider_field_widget_is_radioselect(self):
        form = ExportForm()
        assert isinstance(form.fields["provider"].widget, RadioSelect)

    def test_exportform_provider_field_sets_choices(self):
        form = ExportForm()
        assert form.fields["provider"].choices == TAX_FORM_PROVIDERS

    def test_exportform_provider_field_sets_initial_choice_to_koinly(self):
        form = ExportForm()
        assert form.fields["provider"].initial == "koinly"

    def test_exportform_provider_field_widget_sets_class_with_gap(self):
        form = ExportForm()
        assert form.fields["provider"].widget.attrs["class"] == "with-gap"

    def test_exportform_has_use_mve_field_as_booleanfield(self):
        form = ExportForm()
        assert form.fields.get("use_mve") is not None
        assert isinstance(form.fields["use_mve"], BooleanField)

    def test_exportform_use_mve_field_sets_required_false(self):
        form = ExportForm()
        assert form.fields["use_mve"].required is False

    def test_exportform_use_mve_field_sets_label(self):
        form = ExportForm()
        assert form.fields["use_mve"].label == "Use maximum value engine"

    def test_exportform_use_mve_field_sets_help_text(self):
        form = ExportForm()
        assert form.fields["use_mve"].help_text == TAX_FORM_USE_MVE_HELP_TEXT

    def test_exportform_has_non_zero_field_as_booleanfield(self):
        form = ExportForm()
        assert form.fields.get("non_zero") is not None
        assert isinstance(form.fields["non_zero"], BooleanField)

    def test_exportform_non_zero_field_sets_required_false(self):
        form = ExportForm()
        assert form.fields["non_zero"].required is False

    def test_exportform_non_zero_field_sets_label(self):
        form = ExportForm()
        assert form.fields["non_zero"].label == "Include CSV file with non-zero values"

    def test_exportform_non_zero_field_sets_help_text(self):
        form = ExportForm()
        assert form.fields["non_zero"].help_text == TAX_FORM_NON_ZERO_HELP_TEXT

    # # clean
    def test_exportform_clean_calls_and_returns_super_clean(self):
        form = ExportForm(
            data={"provider": "koinly", "use_mve": True, "non_zero": True}
        )
        form.is_valid()
        returned = form.clean()
        assert returned == {"provider": "koinly", "use_mve": True, "non_zero": True}

    @pytest.mark.parametrize(
        "provider",
        [provider[0] for provider in TAX_FORM_PROVIDERS if provider[0] != "koinly"],
    )
    def test_exportform_clean_raises_validationerror_for_not_implemented_provider(
        self, provider
    ):
        form = ExportForm(
            data={"provider": provider, "use_mve": False, "non_zero": False}
        )
        form.is_valid()
        with pytest.raises(ValidationError) as exception:
            form.clean()
        assert (
            str(exception.value) == "['Only Koinly is available as provider for now.']"
        )


# # USERS
class TestCustomSignupForm:
    """Testing class for :class:`CustomSignupForm`."""

    # # CustomSignupForm
    def test_customsignupform_issubclass_of_form(self):
        assert issubclass(CustomSignupForm, Form)

    # # signup
    def test_customsignupform_overrides_signup_method(self):
        form_class = CustomSignupForm
        assert hasattr(form_class, "signup")


class TestBaseBundleNameForm:
    """Testing class for :class:`BaseBundleNameForm`."""

    # # BaseBundleNameForm
    def test_basebundlenameform_issubclass_of_modelform(self):
        assert issubclass(BaseBundleNameForm, ModelForm)

    def test_basebundlenameform_has_name_field_as_charfield(self):
        form = BaseBundleNameForm()
        assert form.fields.get("name") is not None
        assert isinstance(form.fields["name"], CharField)

    def test_basebundlenameform_has_addresses_field_as_charfield(self):
        form = BaseBundleNameForm()
        assert form.fields.get("addresses") is not None
        assert isinstance(form.fields["addresses"], CharField)

    def test_basebundlenameform_has_public_field_as_booleanfield(self):
        form = BaseBundleNameForm()
        assert form.fields.get("public") is not None
        assert isinstance(form.fields["public"], BooleanField)

    def test_basebundlenameform_name_field_sets_required_true(self):
        form = BaseBundleNameForm()
        assert form.fields["name"].required is True

    def test_basebundlenameform_addresses_field_sets_required_true(self):
        form = BaseBundleNameForm()
        assert form.fields["addresses"].required is True

    def test_basebundlenameform_name_field_widget_is_textinput(self):
        form = BaseBundleNameForm()
        assert isinstance(form.fields["name"].widget, TextInput)

    def test_basebundlenameform_public_field_sets_required_false(self):
        form = BaseBundleNameForm()
        assert form.fields["public"].required is False

    def test_basebundlenameform_public_field_sets_label(self):
        form = BaseBundleNameForm()
        assert form.fields["public"].label == "Public URL"

    def test_basebundlenameform_public_field_sets_help_text(self):
        form = BaseBundleNameForm()
        assert form.fields["public"].help_text == BUNDLENAME_PUBLIC_HELP_TEXT

    def test_basebundlenameform_public_field_widget_is_textinput(self):
        form = BaseBundleNameForm()
        assert isinstance(form.fields["public"].widget, CheckboxInput)

    def test_basebundlenameform_addresses_field_widget_is_textarea(self):
        form = BaseBundleNameForm()
        assert isinstance(form.fields["addresses"].widget, Textarea)

    def test_basebundlenameform_name_field_widget_sets_autofocus(self):
        form = BaseBundleNameForm()
        assert form.fields["name"].widget.attrs["autofocus"] == "autofocus"

    def test_basebundlenameform_name_field_widget_sets_length(self):
        form = BaseBundleNameForm()
        assert form.fields["name"].widget.attrs["length"] == "50"

    def test_basebundlenameform_addresses_field_widget_sets_class(self):
        form = BaseBundleNameForm()
        assert form.fields["addresses"].widget.attrs["class"] == "materialize-textarea"

    def test_basebundlenameform_addresses_field_widget_sets_rows(self):
        form = BaseBundleNameForm()
        assert form.fields["addresses"].widget.attrs["rows"] == 20

    def test_basebundlenameform_addresses_field_widget_sets_placeholder(self):
        form = BaseBundleNameForm()
        assert (
            form.fields["addresses"].widget.attrs["placeholder"]
            == "Enter Algorand addresses and/or .algo names"
        )

    def test_basebundlenameform_meta_fields(self):
        form = BaseBundleNameForm()
        assert form._meta.fields == ("name", "addresses", "public")

    def test_basebundlenameform_meta_model_is_bundlename(self):
        form = BaseBundleNameForm()
        assert form._meta.model == BundleName


class TestProfileBundleNameForm:
    """Testing class for :class:`ProfileBundleNameForm`."""

    # # ProfileBundleNameForm
    def test_profilebundlenameform_issubclass_of_basebundlenameform(self):
        assert issubclass(ProfileBundleNameForm, BaseBundleNameForm)

    # # __init__
    def test_profilebundlenameform_init_calls_super_init(self, mocker):
        mocked = mocker.patch("core.forms.BaseBundleNameForm.__init__")
        ProfileBundleNameForm.instance = mocker.MagicMock()
        ProfileBundleNameForm.fields = {"addresses": mocker.MagicMock()}
        ProfileBundleNameForm(
            mocker.MagicMock(), 2, 5, named1="named1", named2="named2"
        )
        mocked.assert_called_once_with(2, 5, named1="named1", named2="named2")

    def test_profilebundlenameform_init_sets_instance_profile_to_provided(self, mocker):
        mocker.patch("core.forms.BaseBundleNameForm.__init__")
        ProfileBundleNameForm.instance = mocker.MagicMock()
        ProfileBundleNameForm.fields = {"addresses": mocker.MagicMock()}
        for_profile = mocker.MagicMock()
        form = ProfileBundleNameForm(for_profile)
        assert form.instance.profile == for_profile

    def test_profilebundlenameform_init_sets_addresses_help_text(self, mocker):
        mocker.patch("core.forms.BaseBundleNameForm.__init__")
        help_text = mocker.MagicMock()
        mocked_format = mocker.patch(
            "core.forms.format_addresses_limit_help_text", return_value=help_text
        )
        instance = mocker.MagicMock()
        ProfileBundleNameForm.instance = instance
        ProfileBundleNameForm.fields = {"addresses": mocker.MagicMock()}
        for_profile = mocker.MagicMock()
        form = ProfileBundleNameForm(for_profile)
        assert form.fields["addresses"].help_text == help_text
        mocked_format.assert_called_once_with(instance)

    @pytest.mark.django_db
    def test_profilebundlenameform_save_non_unique_name(self):
        user_model = get_user_model()
        user = user_model.objects.create(email="someform1@example.com")
        BundleName.objects.create(
            profile=user.profile,
            name="name1",
            addresses=f"{TEST_ADDRESS} {TEST_ADDRESS2}",
        )
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={
                "name": "name1",
                "addresses": f"{TEST_ADDRESS}",
            },
        )
        assert not form.is_valid()

    @pytest.mark.django_db
    def test_profilebundlenameform_save_non_unique_bundle(self):
        user_model = get_user_model()
        user = user_model.objects.create(email="someform2@example.com")
        BundleName.objects.create(
            profile=user.profile,
            name="name1",
            addresses=f"{TEST_ADDRESS} {TEST_ADDRESS2}",
        )
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={
                "name": "name100",
                "addresses": f"{TEST_ADDRESS2} {TEST_ADDRESS}",
            },
        )
        assert not form.is_valid()

    @pytest.mark.django_db
    def test_profilebundlenameform_save(self):
        user_model = get_user_model()
        user = user_model.objects.create(email="someform1@example.com")
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={
                "name": "some name 1",
                "addresses": f"{TEST_ADDRESS} {TEST_ADDRESS2}",
            },
        )
        bundlename_new = form.save()
        assert bundlename_new == BundleName.objects.all()[0]

    @pytest.mark.django_db
    def test_profilebundlenameform_form_validation_for_too_long_name(self):
        user_model = get_user_model()
        user = user_model.objects.create(email="someform1@example.com")
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={
                "name": "xyz" * 51,
                "addresses": f"{TEST_ADDRESS} {TEST_ADDRESS2}",
            },
        )
        assert form.is_valid() is False
        assert "Ensure this value has at most" in form.errors["name"][0]

    # # clean
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "addresses",
        [
            "foobar",
            "VKENBO5W2DZAZFQR45SOQO6IMWS5UMVZCHLPEACNOII7BDJTGBZKSEL4Y",
            "393537671",
            "#17180006",
        ],
    )
    def test_profilebundlenameform_is_not_valid_for_invalid_address(self, addresses):
        user_model = get_user_model()
        unique = str(time.time())[5:]
        user = user_model.objects.create(email=f"someform{unique}@example.com")
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={"name": f"name{unique}", "addresses": addresses},
        )
        assert not form.is_valid()
        assert form.errors["__all__"][0] == INVALID_ADDRESS_TEXT

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "addresses",
        [
            "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU",
            (
                "VKENBO5W2DZAZFQR45SOQO6IMWS5UMVZCHLPEACNOII7BDJTGBZKSEL4Y4 "
                "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU "
            ),
            (
                "VKENBO5W2DZAZFQR45SOQO6IMWS5UMVZCHLPEACNOII7BDJTGBZKSEL4Y4 "
                "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU "
                "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
            ),
        ],
    )
    def test_profilebundlenameform_is_valid_for_valid_addresses(self, addresses):
        user_model = get_user_model()
        unique = str(time.time())[5:]
        user = user_model.objects.create(email=f"someform{unique}@example.com")
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={"name": f"name{unique}", "addresses": addresses},
        )
        assert form.is_valid()

    @pytest.mark.django_db
    def test_profilebundlenameform_clean_for_missing_name(self, mocker):
        user_model = get_user_model()
        unique = str(time.time())[5:]
        user = user_model.objects.create(email=f"someform{unique}@example.com")
        name = ""
        parsed_addresses = "parsed addresses"
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={"name": name, "addresses": "addresses"},
        )
        mocker.patch("core.forms.addresses_from_raw", return_value=parsed_addresses)
        mocked_address = mocker.patch(
            "core.forms.validate_address_or_algo_name_url_path"
        )
        mocked_system = mocker.patch(
            "core.models.Profile.bundlename_system_reserved_url_path_check"
        )
        mocked_integrity = mocker.patch(
            "core.models.Profile.integrity_check_for_bundlename"
        )
        assert form.is_valid() is False
        mocked_system.assert_not_called()
        mocked_address.assert_not_called()
        mocked_integrity.assert_not_called()

    @pytest.mark.django_db
    def test_profilebundlenameform_clean_calls_validate_address_or_algo_name_url_path(
        self, mocker
    ):
        user_model = get_user_model()
        unique = str(time.time())[5:]
        user = user_model.objects.create(email=f"someform{unique}@example.com")
        name = "name.algo"
        parsed_addresses = "parsed addresses"
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={"name": name, "addresses": "addresses"},
        )
        mocker.patch("core.forms.addresses_from_raw", return_value=parsed_addresses)
        mocked_address = mocker.patch(
            "core.forms.validate_address_or_algo_name_url_path"
        )
        assert form.is_valid()
        mocked_address.assert_called_once_with(name)

    @pytest.mark.django_db
    def test_profilebundlenameform_clean_calls_bundlename_system_reserved_url_check(
        self, mocker
    ):
        user_model = get_user_model()
        unique = str(time.time())[5:]
        user = user_model.objects.create(email=f"someform{unique}@example.com")
        name = "name"
        parsed_addresses = "parsed addresses"
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={"name": name, "addresses": "addresses"},
        )
        mocker.patch("core.forms.addresses_from_raw", return_value=parsed_addresses)
        mocked_system = mocker.patch(
            "core.models.Profile.bundlename_system_reserved_url_path_check"
        )
        assert form.is_valid()
        mocked_system.assert_called_once_with(name)

    @pytest.mark.django_db
    def test_profilebundlenameform_clean_calls_profile_integrity_check_for_bundlename(
        self, mocker
    ):
        user_model = get_user_model()
        unique = str(time.time())[5:]
        user = user_model.objects.create(email=f"someform{unique}@example.com")
        name = "name"
        parsed_addresses = "parsed addresses"
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={"name": name, "addresses": "addresses"},
        )
        mocker.patch("core.forms.addresses_from_raw", return_value=parsed_addresses)
        mocked_integrity = mocker.patch(
            "core.models.Profile.integrity_check_for_bundlename"
        )
        mocked_integrity_public = mocker.patch(
            "core.models.Profile.integrity_check_for_public_bundlename"
        )
        assert form.is_valid()
        mocked_integrity.assert_called_once_with(
            None, {"name": name, "addresses": parsed_addresses, "public": False}
        )
        mocked_integrity_public.assert_not_called()

    @pytest.mark.django_db
    def test_profilebundlenameform_clean_calls_profile_integrity_check_for_public(
        self, mocker
    ):
        user_model = get_user_model()
        unique = str(time.time())[5:]
        user = user_model.objects.create(email=f"someform{unique}@example.com")
        name = "name"
        parsed_addresses = "parsed addresses"
        form = ProfileBundleNameForm(
            for_profile=user.profile,
            data={"name": name, "addresses": "addresses", "public": True},
        )
        mocker.patch("core.forms.addresses_from_raw", return_value=parsed_addresses)
        mocked_integrity = mocker.patch(
            "core.models.Profile.integrity_check_for_bundlename"
        )
        mocked_integrity_public = mocker.patch(
            "core.models.Profile.integrity_check_for_public_bundlename"
        )
        assert form.is_valid()
        mocked_integrity.assert_called_once_with(
            None, {"name": name, "addresses": parsed_addresses, "public": True}
        )
        mocked_integrity_public.assert_called_once_with(
            None, {"name": name, "addresses": parsed_addresses, "public": True}
        )


class TestDeactivateProfileForm:
    """Testing class for :class:`DeactivateProfileForm`."""

    # # DeactivateProfileForm
    def test_deactivateprofileform_issubclass_of_form(self):
        assert issubclass(DeactivateProfileForm, Form)

    def test_deactivateprofileform_has_captcha_as_field_label(self):
        form = DeactivateProfileForm()
        assert form.fields.get("captcha") is not None
        assert isinstance(form.fields["captcha"], CaptchaField)

    # # deactivate_profile
    def test_deactivateprofileform_deactivate_profile_sets_request_deactivates_user(
        self, mocker
    ):
        request = mocker.MagicMock()
        request.user.is_active = True
        DeactivateProfileForm().deactivate_profile(request)
        assert request.user.is_active is False

    def test_deactivateprofileform_deactivate_profile_logouts_user(self, mocker):
        mocked = mocker.patch("core.forms.logout")
        request = mocker.MagicMock()
        DeactivateProfileForm().deactivate_profile(request)
        mocked.assert_called_once_with(request)


class TestUpdateUserForm:
    """Testing class for :class:`UpdateUserForm`."""

    # # UpdateUserForm
    def test_updateuserform_issubclass_of_modelform(self):
        assert issubclass(UpdateUserForm, ModelForm)

    # # Meta
    def test_updateuserform_meta_fields(self):
        form = UpdateUserForm()
        assert form._meta.fields == ("first_name", "last_name")

    def test_updateuserform_meta_model_is_user(self):
        form = UpdateUserForm()
        assert form._meta.model == User

    def test_updateuserform_first_name_field_has_suggestion_as_label(self):
        form = UpdateUserForm()
        assert form.fields["first_name"].label == "First name"

    def test_updateuserform_last_name_field_has_suggestion_as_label(self):
        form = UpdateUserForm()
        assert form.fields["last_name"].label == "Last name"

    def test_updateuserform_form_validation_for_too_long_user_first_name(self):
        form = UpdateUserForm(data={"first_name": "xyz" * 51, "last_name": "last_name"})
        assert form.is_valid() is False
        assert form.errors["first_name"] == [TOO_LONG_USER_FIRST_NAME_ERROR]

    def test_updateuserform_form_validation_for_too_long_user_last_name(self):
        form = UpdateUserForm(data={"first_name": "first_name", "last_name": "x" * 151})
        assert form.is_valid() is False
        assert form.errors["last_name"] == [TOO_LONG_USER_LAST_NAME_ERROR]

    # # save
    @pytest.mark.django_db
    def test_updateuserform_save(self):
        user_model = get_user_model()
        user = user_model.objects.create(email="edituser@example.com")
        form = UpdateUserForm(data={"first_name": "John", "last_name": "Doe"})
        form.instance = user
        form.save()
        assert user_model.objects.all()[0].first_name == "John"


class TestProfileInlineForm:
    """Testing class for :class:`ProfileInlineForm`."""

    # # ProfileInlineForm
    def test_profileinlineform_issubclass_of_baseinlineformset(self):
        assert issubclass(ProfileInlineForm, BaseInlineFormSet)

    def test_core_forms_profileinlineform_clean_for_invalid_address(self, mocker):
        formset = ProfileInlineForm.__new__(ProfileInlineForm)
        formset.forms = [mocker.MagicMock()]
        mocker.patch.object(
            ProfileInlineForm,
            "cleaned_data",
            new_callable=mocker.PropertyMock,
            return_value=[{"address": "X"}],
        )
        mocker.patch("core.forms.check_algorand_address", return_value="")
        with pytest.raises(ValidationError):
            formset.clean()
        formset.forms[0].add_error.assert_called_once_with(
            "address", INVALID_ADDRESS_TEXT
        )


class TestProfileFormSet:
    """Testing class for ProfileFormSet instance."""

    def test_profileformset_instance_is_user(self):
        formset = ProfileFormSet()
        assert isinstance(formset.instance, User)

    def test_profileformset_model_is_profile(self):
        formset = ProfileFormSet()
        assert formset.model == Profile

    def test_profileformset_address_field(self):
        formset = ProfileFormSet()
        assert "address" in formset.form.base_fields
        assert isinstance(formset.address, CharField)
        assert formset.address.widget.attrs == {"maxlength": "58"}
        assert formset.address.error_messages.get("required")


class TestProfileRouterForm:
    """Testing class for :class:`ProfileRouterForm`."""

    def test_profilerouterform_issubclass_of_modelform(self):
        assert issubclass(ProfileRouterForm, ModelForm)

    def test_profilerouterform_meta_model_and_fields(self):
        assert ProfileRouterForm.Meta.model is Profile
        assert ProfileRouterForm.Meta.fields == ("preferred_router",)

    def test_profilerouterform_choices_come_from_swap_routers(self, mocker):
        mocker.patch("core.forms.swap_routers", return_value=[("folks", "Folks")])
        form = ProfileRouterForm()
        assert isinstance(form.fields["preferred_router"], ChoiceField)
        assert form.fields["preferred_router"].choices == [("folks", "Folks")]


class TestProfileExplorerForm:
    """Testing class for :class:`ProfileExplorerForm`."""

    def test_profileexplorerform_issubclass_of_modelform(self):
        assert issubclass(ProfileExplorerForm, ModelForm)

    def test_profileexplorerform_meta_model_and_fields(self):
        assert ProfileExplorerForm.Meta.model is Profile
        assert ProfileExplorerForm.Meta.fields == ("preferred_explorer",)

    def test_profileexplorerform_choices_come_from_registry(self):
        form = ProfileExplorerForm()
        assert isinstance(form.fields["preferred_explorer"], ChoiceField)
        assert form.fields["preferred_explorer"].choices[0] == ("allo", "Allo")

    def test_profileexplorerform_accepts_known_explorer(self):
        form = ProfileExplorerForm(data={"preferred_explorer": "lora"})
        assert form.is_valid() is True

    def test_profileexplorerform_rejects_unknown_explorer(self):
        form = ProfileExplorerForm(data={"preferred_explorer": "bogus"})
        assert form.is_valid() is False
