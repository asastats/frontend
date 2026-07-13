"""Testing module for :py:mod:`website.core.views` module."""

import time
from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.http import (
    Http404,
    HttpResponseRedirect,
    HttpResponseServerError,
    QueryDict,
)
from django.test import RequestFactory
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import DeleteView, FormView
from redis import BusyLoadingError

from api.client import BackendError
from core.forms import (
    DeactivateProfileForm,
    ProfileBundleNameForm,
    ProfileFormSet,
    UpdateUserForm,
)
from core.models import BundleName, Profile
from core.permissions import (
    CanAccessApiMixin,
    CanAccessAuthorizeMixin,
    CanAddBundleNameMixin,
    CanUseBundleNamesMixin,
)
from core.views import (
    AboutView,
    AddressView,
    AddressViewCustom,
    AnsView,
    ASMPrivacyView,
    BaseAddressView,
    BaseStaticPageView,
    BundleNameAddDisplay,
    BundleNameAddView,
    BundleNameCreate,
    BundleNameDeleteView,
    BundleNameDisplay,
    BundleNameEditView,
    BundleNameUpdate,
    BundleNameView,
    DeactivateProfileView,
    DisclaimerView,
    ExportDownloadForm,
    ExportForm,
    ExportView,
    FaqView,
    FeaturesView,
    HomePageView,
    IndexView,
    NameServiceView,
    NfdView,
    ProfileAccountView,
    ProfileApiView,
    ProfileAuthorizeCheckView,
    ProfileAuthorizeView,
    ProfileDisplay,
    ProfileEditView,
    ProfilePermissionFetchView,
    ProfileUpdate,
    SubscriptionsView,
    TokenomicsView,
    custom_server_error,
    export_download,
    html_file,
)
from utils.constants.core import ALGORAND_WALLETS
from utils.constants.nameservice import NAME_SERVICE_MULTIPLE
from utils.constants.users import (
    AUTHORIZATION_TRANSACTION_CONFIRMED_MESSAGE,
    AUTHORIZATION_TRANSACTION_ERROR_MESSAGE,
    BUNDLE_NAME_DELETED_MESSAGE,
    BUNDLE_NAME_NOT_FOUND_ERROR,
)
from utils.tests.fixtures import (
    TEST_ADDRESS,
    TEST_ADDRESS2,
    TEST_ADDRESS_EVM,
    TEST_ADDRESS_XCHAIN,
    TEST_BUNDLE,
    TEST_NEW_BUNDLE,
)

from .test_views import get_user_edit_fake_post_data

user_model = get_user_model()


class TestCustomErrorHandlers:
    # custom_server_error
    @pytest.mark.parametrize(
        "typ",
        [BusyLoadingError, ConnectionError],
    )
    def test_core_views_custom_server_error_renders_template_500r(self, typ, mocker):
        request = mocker.MagicMock()
        request.path = "error_path"
        with (
            mock.patch("core.views.loader.get_template") as mocked_template,
            mock.patch(
                "core.views.sys.exc_info", return_value=(typ, None, None)
            ) as mocked_info,
            mock.patch("core.views.logger") as mocked_logger,
        ):
            returned = custom_server_error(request)
            assert isinstance(returned, HttpResponseServerError)
            mocked_template.assert_called_once_with("500r.html")
            mocked_info.assert_called_once_with()
            mocked_logger.warning.assert_called_once_with(
                f"Server error 500 - {str(typ)} - for path '{request.path}'!"
            )

    @pytest.mark.parametrize(
        "typ",
        [NotImplemented, ValueError, KeyError],
    )
    def test_core_views_custom_server_error_renders_template_500(self, typ, mocker):
        mocked = mocker.patch("core.views.HttpResponseServerError")
        with (
            mock.patch("core.views.loader.get_template") as mocked_template,
            mock.patch("core.views.sys.exc_info", return_value=(typ, None, None)),
            mock.patch("core.views.logger") as mocked_logger,
        ):
            returned = custom_server_error(mocker.MagicMock())
            assert returned == mocked.return_value
            mocked.assert_called_once_with(
                mocked_template.return_value.render.return_value
            )
            mocked_template.assert_called_once_with("500.html")
            mocked_logger.assert_not_called()


class BaseView:
    """Base helper class for testing custom views."""

    def setup_view(self, view, request, *args, **kwargs):
        """Mimic as_view() returned callable, but returns view instance.

        args and kwargs are the same as those passed to ``reverse()``

        """
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view

    # # helper methods
    def setup_method(self):
        # Setup request
        self.request = RequestFactory().get("/fake-path")


class BasePostDownloadView:
    """Base helper class for testing post download views."""

    def setup_view(self, view, request, *args, **kwargs):
        """Mimic as_view() returned callable, but returns view instance.

        args and kwargs are the same as those passed to ``reverse()``

        """
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view

    # # helper methods
    def setup_method(self):
        # Setup request
        self.request = RequestFactory().post("/submit/", {"download": "1"})


class BasePostRefreshView:
    """Base helper class for testing post refresh views."""

    def setup_view(self, view, request, *args, **kwargs):
        """Mimic as_view() returned callable, but returns view instance.

        args and kwargs are the same as those passed to ``reverse()``

        """
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view

    # # helper methods
    def setup_method(self):
        # Setup request
        self.request = RequestFactory().post("/submit/", {"refresh": "1"})


class BaseUserCreatedView(BaseView):
    def setup_method(self):
        # # Setup user
        username = "user{}".format(str(time.time())[5:])
        self.user = user_model.objects.create(
            email="{}@testuser.com".format(username),
            username=username,
        )
        # Setup request
        self.request = RequestFactory().get("/fake-path")
        self.request.user = self.user

    def create_bundlename(self):
        prefix = str(time.time())[-5:]
        return BundleName.objects.create(
            profile=self.user.profile,
            name="name-{}".format(prefix),
            addresses=f"{TEST_ADDRESS} {TEST_ADDRESS2}",
        )


class TestCoreViewsHtmlFile(BaseView):
    """Testing class for :func:`core.views.html_file`."""

    def test_core_views_html_file_functionality(self, mocker):
        mocked_render = mocker.patch("core.views.render")
        returned = html_file(self.request, "auth_terms.html")
        assert returned == mocked_render.return_value
        mocked_render.assert_called_once_with(self.request, "static/auth_terms.html")


class TestIndexView(BaseView):
    """Testing class for :class:`core.views.IndexView`."""

    def test_core_views_indexview_get_context_data(self, mocker):
        # Setup view
        view = IndexView()
        view = self.setup_view(view, self.request)
        slogan = "slogan"
        mocked = mocker.patch("core.views.random_slogan", return_value=slogan)
        context = view.get_context_data()
        mocked.assert_called_once_with()
        # Check.
        assert context["header"] == slogan


class TestIndexViewBranches(BaseView):
    """Testing class for :class:`core.views.IndexView` uncovered branches."""

    def test_core_views_indexview_form_invalid_for_name_service_multiple(self, mocker):
        view = self.setup_view(IndexView(), self.request)
        self.request.POST = QueryDict(mutable=True)
        form = mocker.MagicMock()
        form.errors.get.return_value = [f"x{NAME_SERVICE_MULTIPLE}ADDR"]
        mocked_form_class = mocker.patch.object(IndexView, "form_class")
        mocked_super = mocker.patch("core.views.FormView.form_invalid")
        returned = view.form_invalid(form)
        assert returned == mocked_super.return_value
        mocked_form_class.return_value.add_error.assert_called_once_with(
            "bundle", "ADDR"
        )
        mocked_super.assert_called_once_with(mocked_form_class.return_value)

    def test_core_views_indexview_get_success_url_for_bundle(self, mocker):
        view = self.setup_view(IndexView(), self.request)
        view.addresses = "ADDR1 ADDR2"
        mocked_bundle = mocker.patch("core.views.create_bundle", return_value="HASH")
        mocked_reverse = mocker.patch("core.views.reverse", return_value="/HASH")
        returned = view.get_success_url()
        assert returned == "/HASH"
        mocked_bundle.assert_called_once_with("ADDR1 ADDR2")
        mocked_reverse.assert_called_once_with("bundle", args=["HASH"])


class TestAnsView(BaseView):
    """Testing class for :class:`core.views.AnsView`."""

    def test_core_views_ansview_dispatch_for_single_address_name(self, mocker):
        # Setup view
        view = AnsView()
        name = "name.algo"
        view = self.setup_view(view, self.request, name)
        addresses = f"{TEST_ADDRESS} {TEST_ADDRESS2}"
        mocked = mocker.patch(
            "core.views.check_algorand_address",
            return_value=addresses,
        )
        bundle = "1AD20F5B5C299A0C8B1A50CE0844ED8BC54CC7A2"
        mocked_bundle = mocker.patch(
            "core.views.create_bundle",
            return_value=bundle,
        )
        response = view.dispatch(self.request, name)
        mocked.assert_called_once_with(name + "/ans")
        mocked_bundle.assert_called_once_with(addresses)
        # Check.
        assert view.pattern_name == "bundle"
        assert response.status_code == 302
        assert response.url == f"/{bundle}"

    def test_core_views_ansview_dispatch_for_multiple_addresses_name(self, mocker):
        # Setup view
        view = AnsView()
        name = "namemulti.algo"
        view = self.setup_view(view, self.request, name)
        mocked = mocker.patch(
            "core.views.check_algorand_address", return_value=TEST_ADDRESS
        )
        response = view.dispatch(self.request, name)
        mocked.assert_called_once_with(name + "/ans")
        # Check.
        assert view.pattern_name == "address"
        assert response.status_code == 302
        assert response.url == f"/{TEST_ADDRESS}"

    def test_core_views_ansview_dispatch_for_invalid_name(self, mocker):
        # Setup view
        view = AnsView()
        name = "foobarans.algo"
        view = self.setup_view(view, self.request, name)
        mocked = mocker.patch("core.views.check_algorand_address", return_value="")
        response = view.dispatch(self.request, name)
        mocked.assert_called_once_with(name + "/ans")
        # Check.
        assert view.pattern_name == "address"
        assert response.status_code == 302
        assert response.url == "/"

    def test_core_views_ansview_get_redirect_url_for_valid_address(self, mocker):
        # Setup view
        view = AnsView()
        address = TEST_ADDRESS
        view = self.setup_view(view, self.request, address)
        mocked = mocker.patch("core.views.is_valid_address", return_value=True)
        context = view.get_redirect_url(address)
        mocked.assert_called_once_with(address)
        # Check.
        assert context == f"/{address}"

    def test_core_views_ansview_get_redirect_url_for_bundle(self, mocker):
        # Setup view
        view = AnsView()
        bundle = "1AD20F5B5C299A0C8B1A50CE0844ED8BC54CC7A2"
        view = self.setup_view(view, self.request, bundle)
        view.pattern_name = "bundle"
        mocked = mocker.patch("core.views.is_valid_address")
        context = view.get_redirect_url(bundle)
        mocked.assert_not_called()
        # Check.
        assert context == f"/{bundle}"

    def test_core_views_ansview_get_redirect_url_for_invalid_address(self, mocker):
        # Setup view
        view = AnsView()
        address = ""
        view = self.setup_view(view, self.request, address)
        mocked = mocker.patch("core.views.is_valid_address", return_value=False)
        context = view.get_redirect_url(address)
        mocked.assert_called_once_with(address)
        # Check.
        assert context == "/"


class TestNfdView(BaseView):
    """Testing class for :class:`core.views.NfdView`."""

    def test_core_views_nfdview_dispatch_for_single_address_name(self, mocker):
        # Setup view
        view = NfdView()
        name = "name.algo"
        view = self.setup_view(view, self.request, name)
        addresses = f"{TEST_ADDRESS} {TEST_ADDRESS2}"
        mocked = mocker.patch(
            "core.views.check_algorand_address",
            return_value=addresses,
        )
        bundle = "1AD20F5B5C299A0C8B1A50CE0844ED8BC54CC7A2"
        mocked_bundle = mocker.patch(
            "core.views.create_bundle",
            return_value=bundle,
        )
        response = view.dispatch(self.request, name)
        mocked.assert_called_once_with(name + "/nfd")
        mocked_bundle.assert_called_once_with(addresses)
        # Check.
        assert view.pattern_name == "bundle"
        assert response.status_code == 302
        assert response.url == f"/{bundle}"

    def test_core_views_nfdview_dispatch_for_multiple_addresses_name(self, mocker):
        # Setup view
        view = NfdView()
        name = "namemulti.algo"
        view = self.setup_view(view, self.request, name)
        mocked = mocker.patch(
            "core.views.check_algorand_address", return_value=TEST_ADDRESS
        )
        response = view.dispatch(self.request, name)
        mocked.assert_called_once_with(name + "/nfd")
        # Check.
        assert view.pattern_name == "address"
        assert response.status_code == 302
        assert response.url == f"/{TEST_ADDRESS}"

    def test_core_views_nfdview_dispatch_for_invalid_name(self, mocker):
        # Setup view
        view = NfdView()
        name = "foobarnfd.algo"
        view = self.setup_view(view, self.request, name)
        mocked = mocker.patch("core.views.check_algorand_address", return_value="")
        response = view.dispatch(self.request, name)
        mocked.assert_called_once_with(name + "/nfd")
        # Check.
        assert view.pattern_name == "address"
        assert response.status_code == 302
        assert response.url == "/"

    def test_core_views_nfdview_get_redirect_url_for_valid_address(self, mocker):
        # Setup view
        view = NfdView()
        address = TEST_ADDRESS
        view = self.setup_view(view, self.request, address)
        mocked = mocker.patch("core.views.is_valid_address", return_value=True)
        context = view.get_redirect_url(address)
        mocked.assert_called_once_with(address)
        # Check.
        assert context == f"/{address}"

    def test_core_views_nfdview_get_redirect_url_for_bundle(self, mocker):
        # Setup view
        view = NfdView()
        bundle = "1AD20F5B5C299A0C8B1A50CE0844ED8BC54CC7A2"
        view = self.setup_view(view, self.request, bundle)
        view.pattern_name = "bundle"
        mocked = mocker.patch("core.views.is_valid_address")
        context = view.get_redirect_url(bundle)
        mocked.assert_not_called()
        # Check.
        assert context == f"/{bundle}"

    def test_core_views_nfdview_get_redirect_url_for_invalid_address(self, mocker):
        # Setup view
        view = NfdView()
        address = ""
        view = self.setup_view(view, self.request, address)
        mocked = mocker.patch("core.views.is_valid_address", return_value=False)
        context = view.get_redirect_url(address)
        mocked.assert_called_once_with(address)
        # Check.
        assert context == "/"


class TestNameServiceView(BaseView):
    """Testing class for :class:`core.views.NameServiceView`."""

    def test_core_views_nameserviceview_dispatch_for_valid_name(self, mocker):
        # Setup view
        view = NameServiceView()
        name = "name.algo"
        view = self.setup_view(view, self.request, name)
        mocked = mocker.patch(
            "core.views.check_algorand_address", return_value=TEST_ADDRESS
        )
        response = view.dispatch(self.request, name)
        mocked.assert_called_once_with(name)
        # Check.
        assert response.status_code == 302
        assert response.url == f"/{TEST_ADDRESS}"

    def test_core_views_nameserviceview_dispatch_for_invalid_name(self, mocker):
        # Setup view
        view = NameServiceView()
        name = "foobarnfd.algo"
        view = self.setup_view(view, self.request, name)
        mocked = mocker.patch("core.views.check_algorand_address", return_value="")
        response = view.dispatch(self.request, name)
        mocked.assert_called_once_with(name)
        # Check.
        assert response.status_code == 302
        assert response.url == "/"


class TestNameServiceViewValidationError(BaseView):
    """Testing class for :class:`core.views.NameServiceView` error fallback."""

    def test_core_views_nameserviceview_dispatch_for_validation_error(self, mocker):
        view = self.setup_view(NameServiceView(), self.request, "name.algo")
        self.request.POST = QueryDict(mutable=True)
        mocker.patch(
            "core.views.BaseNameServiceView.dispatch",
            side_effect=ValidationError("x"),
        )
        mocked_form = mocker.patch("core.views.AddressForm")
        mocked_render = mocker.patch("core.views.render")
        returned = view.dispatch(self.request, "name.algo")
        assert returned == mocked_render.return_value
        mocked_render.assert_called_once_with(
            self.request, "index.html", {"form": mocked_form.return_value}
        )


class TestAddressView:
    """Testing class for :class:`core.views.AddressView`."""

    def test_core_views_addressview_is_subclass_of_baseaddresview(self):
        assert issubclass(AddressView, BaseAddressView)


class TestAddressViewCustom:
    """Testing class for :class:`core.views.AddressViewCustom`."""

    def test_core_views_addressviewcustom_is_subclass_of_baseaddresview(self):
        assert issubclass(AddressViewCustom, BaseAddressView)


# # STATIC PAGES
class TestBaseStaticPageView(BaseView):
    """Testing class for :class:`core.views.BaseStaticPageView`."""

    def test_core_views_basestaticpageview_is_subclass_of_templateview(self):
        assert issubclass(BaseStaticPageView, TemplateView)

    # # get_context_data
    def test_core_views_basestaticpageview_get_context_data_for_dark_mode(self, mocker):
        # Setup view
        view = BaseStaticPageView()
        tempdict = self.request.GET.copy()
        tempdict["dark"] = "dark"
        self.request.GET = tempdict
        view = self.setup_view(view, self.request)
        context = view.get_context_data()
        # Check.
        assert context["mode"] == "dark"

    def test_core_views_basestaticpageview_get_context_data_for_light_mode(
        self, mocker
    ):
        # Setup view
        view = BaseStaticPageView()
        view = self.setup_view(view, self.request)
        context = view.get_context_data()
        # Check.
        assert context.get("mode") is None


class TestAboutView:
    """Testing class for :class:`core.views.AboutView`."""

    def test_core_views_aboutview_is_subclass_of_basestaticpageview(self):
        assert issubclass(AboutView, BaseStaticPageView)

    def test_core_views_aboutview_sets_template_name(self):
        assert AboutView.template_name == "about.html"


class TestDisclaimerView:
    """Testing class for :class:`core.views.DisclaimerView`."""

    def test_core_views_disclaimerview_is_subclass_of_basestaticpageview(self):
        assert issubclass(DisclaimerView, BaseStaticPageView)

    def test_core_views_disclaimerview_sets_template_name(self):
        assert DisclaimerView.template_name == "disclaimer.html"


class TestFaqView:
    """Testing class for :class:`core.views.FaqView`."""

    def test_core_views_faqview_is_subclass_of_basestaticpageview(self):
        assert issubclass(FaqView, BaseStaticPageView)

    def test_core_views_faqview_sets_template_name(self):
        assert FaqView.template_name == "faq.html"


class TestFeaturesView:
    """Testing class for :class:`core.views.FeaturesView`."""

    def test_core_views_featuresview_is_subclass_of_basestaticpageview(self):
        assert issubclass(FeaturesView, BaseStaticPageView)

    def test_core_views_featuresview_sets_template_name(self):
        assert FeaturesView.template_name == "features.html"


class TestSubscriptionsFaqView:
    """Testing class for :class:`core.views.SubscriptionsView`."""

    def test_core_views_subscriptionsview_is_subclass_of_basestaticpageview(self):
        assert issubclass(SubscriptionsView, BaseStaticPageView)

    def test_core_views_subscriptionsview_sets_template_name(self):
        assert SubscriptionsView.template_name == "subscriptions.html"


class TestTokenomicsView(BaseView):
    """Testing class for :class:`core.views.TokenomicsView`."""

    def test_core_views_tokenomicsview_is_subclass_of_templateview(self):
        assert issubclass(TokenomicsView, TemplateView)

    # # get_context_data
    def test_core_views_tokenomicsview_get_context_data(self, mocker):
        # Setup view
        view = TokenomicsView()
        view = self.setup_view(view, self.request)
        price = 500.0

        mocked_price = mocker.patch("core.views.fetch_price", return_value=price)
        mocked_reports = mocker.patch(
            "core.views.load_transparency_reports", return_value=["mocked_report"]
        )

        context = view.get_context_data()

        mocked_price.assert_called_once_with()
        mocked_reports.assert_called_once_with()
        # Check.
        assert context["price"] == price
        assert context["transparency_reports"] == ["mocked_report"]

    def test_core_views_tokenomicsview_get_context_data_for_dark_mode(self, mocker):
        # Setup view
        view = TokenomicsView()
        tempdict = self.request.GET.copy()
        tempdict["dark"] = "dark"
        self.request.GET = tempdict
        view = self.setup_view(view, self.request)

        mocker.patch("core.views.fetch_price")
        mocker.patch("core.views.load_transparency_reports")

        context = view.get_context_data()
        # Check.
        assert context["mode"] == "dark"

    def test_core_views_tokenomicsview_get_context_data_for_light_mode(self, mocker):
        # Setup view
        view = TokenomicsView()
        view = self.setup_view(view, self.request)

        mocker.patch("core.views.fetch_price")
        mocker.patch("core.views.load_transparency_reports")

        context = view.get_context_data()
        # Check.
        assert context.get("mode") is None


class TestASMPrivacyView:
    """Testing class for :class:`core.views.ASMPrivacyView`."""

    def test_core_views_asmprivacyview_is_subclass_of_basestaticpageview(self):
        assert issubclass(ASMPrivacyView, BaseStaticPageView)

    def test_core_views_asmprivacyview_sets_template_name(self):
        assert ASMPrivacyView.template_name == "asm-privacy.html"


# # TAX
class TestExportView(BaseView):
    """Testing class for :class:`core.views.ExportView`."""

    def test_core_views_exportview_is_subclass_of_templateview(self):
        assert issubclass(ExportView, FormView)

    # # dispatch
    def test_core_views_exportview_dispatch_for_empty_addresses(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        # Run.
        mocked_bundle = mocker.patch(
            "core.views.check_bundle_addresses", return_value=""
        )
        mocked_create = mocker.patch("core.views.create_bundle")
        view_object = view.dispatch(self.request, [TEST_BUNDLE])
        # Check.
        assert view_object.status_code == 302
        assert view_object.url == "/"
        mocked_bundle.assert_called_once_with(TEST_BUNDLE)
        mocked_create.assert_not_called()

    def test_core_views_exportview_dispatch_for_old_bundle(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        # Run.
        mocked_bundle = mocker.patch(
            "core.views.check_bundle_addresses",
            return_value=f"{TEST_ADDRESS} {TEST_ADDRESS2}",
        )
        mocked_create = mocker.patch(
            "core.views.create_bundle", return_value=TEST_NEW_BUNDLE
        )
        view_object = view.dispatch(self.request, [TEST_BUNDLE])
        # Check.
        assert view_object.status_code == 302
        assert view_object.url == f"/export/{TEST_NEW_BUNDLE}/"
        mocked_bundle.assert_called_once_with(TEST_BUNDLE)
        mocked_create.assert_called_once_with(f"{TEST_ADDRESS} {TEST_ADDRESS2}")

    def test_core_views_exportview_dispatch_for_valid_address(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_ADDRESS)
        # Run.
        mocked_bundle = mocker.patch("core.views.check_bundle_addresses")
        mocked_create = mocker.patch("core.views.create_bundle")
        mocked_export = mocker.patch("core.views.check_export_status")
        view_object = view.dispatch(self.request, [TEST_ADDRESS])
        # Check.
        assert view_object.status_code == 200
        assert view._tax_data == mocked_export.return_value
        mocked_export.assert_called_once_with(TEST_ADDRESS)
        mocked_bundle.assert_not_called()
        mocked_create.assert_not_called()

    def test_core_views_exportview_dispatch_for_valid_bundle(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_NEW_BUNDLE)
        # Run.
        mocker.patch("core.helpers.check_bundle_addresses")
        mocked_bundle = mocker.patch(
            "core.views.check_bundle_addresses",
            return_value=f"{TEST_ADDRESS} {TEST_ADDRESS2}",
        )
        mocked_create = mocker.patch(
            "core.views.create_bundle", return_value=TEST_NEW_BUNDLE
        )
        mocked_export = mocker.patch("core.views.check_export_status")
        view_object = view.dispatch(self.request, [TEST_NEW_BUNDLE])
        # Check.
        assert view_object.status_code == 200
        assert view._tax_data == mocked_export.return_value
        mocked_export.assert_called_once_with(TEST_NEW_BUNDLE)
        mocked_bundle.assert_called_once_with(TEST_NEW_BUNDLE)
        mocked_create.assert_called_once_with(f"{TEST_ADDRESS} {TEST_ADDRESS2}")

    # # form_invalid
    def test_core_views_exportview_form_invalid_functionality(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        # Run.
        mocker.patch("core.helpers.check_bundle_addresses")
        form = mocker.MagicMock()
        mocked_delete = mocker.patch("core.views.reset_export")
        response = view.form_invalid(form)
        # Check.
        assert response.status_code == 200
        mocked_delete.assert_not_called()

    # # form_valid
    def test_core_views_exportview_form_valid_functionality(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        # Run.
        form = mocker.MagicMock()
        form.cleaned_data = {"provider": "provider", "use_mve": True, "non_zero": True}
        mocked_delete = mocker.patch("core.views.reset_export")
        mocked_success = mocker.patch("core.views.ExportView.get_success_url")
        mocked_response = mocker.patch("core.views.HttpResponseRedirect")
        view_object = view.form_valid(form)
        # Check.
        assert view_object == mocked_response.return_value
        mocked_success.assert_called_once_with(
            typ="process", provider="provider", use_mve=True, non_zero=True
        )
        mocked_response.assert_called_once_with(mocked_success.return_value)
        mocked_delete.assert_not_called()

    # # get_context_data
    def test_core_views_exportview_get_context_data_for_address(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_ADDRESS)
        mocked_prepare = mocker.patch("core.views.prepare_tax_context")
        # Run.
        context = view.get_context_data()
        # Check.
        assert context == mocked_prepare.return_value
        assert mocked_prepare.call_args_list[0][0][0].get("view") == view
        assert isinstance(
            mocked_prepare.call_args_list[0][0][0].get("form"), ExportForm
        )
        assert mocked_prepare.call_args_list[0][0][1] == TEST_ADDRESS

    def test_core_views_exportview_get_context_data_for_bundle(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        mocked_prepare = mocker.patch("core.views.prepare_tax_context")
        # Run.
        context = view.get_context_data()
        # Check.
        assert context == mocked_prepare.return_value
        assert mocked_prepare.call_args_list[0][0][0].get("view") == view
        assert isinstance(
            mocked_prepare.call_args_list[0][0][0].get("form"), ExportForm
        )
        assert mocked_prepare.call_args_list[0][0][1] == TEST_BUNDLE

    def test_core_views_exportview_get_context_data_for_finished_tax(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        tax_report = "tax_report"
        view._tax_data = {"finished_tax": False, "tax_report": tax_report}
        mocked_prepare = mocker.patch("core.views.prepare_tax_context")
        # Run.
        context = view.get_context_data()
        # Check.
        assert context == mocked_prepare.return_value
        # Check.
        assert mocked_prepare.call_args_list[0][0][0].get("view") == view
        assert isinstance(
            mocked_prepare.call_args_list[0][0][0].get("form"), ExportDownloadForm
        )
        assert mocked_prepare.call_args_list[0][0][0].get("finished_tax") == tax_report
        assert mocked_prepare.call_args_list[0][0][1] == TEST_BUNDLE

    def test_core_views_exportview_get_context_data_for_processing_tax(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_ADDRESS)
        view._tax_data = {"processing_tax": TEST_ADDRESS}
        mocked_prepare = mocker.patch("core.views.prepare_tax_context")
        # Run.
        context = view.get_context_data()
        # Check.
        assert context == mocked_prepare.return_value
        # Check.
        assert mocked_prepare.call_args_list[0][0][0].get("view") == view
        assert isinstance(
            mocked_prepare.call_args_list[0][0][0].get("form"), ExportForm
        )
        assert (
            mocked_prepare.call_args_list[0][0][0].get("processing_tax") == TEST_ADDRESS
        )
        assert mocked_prepare.call_args_list[0][0][1] == TEST_ADDRESS

    def test_core_views_exportview_get_context_data_for_analysis_tax(self, mocker):
        # Setup view
        view = ExportView()
        analysis_data = {
            "errors": 2,
            "unprocessed": 0,
            "non_eligible": [],
            "locked": [TEST_ADDRESS, TEST_ADDRESS2],
            "file_error": [],
        }
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        view._tax_data = {"analysis_tax": analysis_data}
        mocked_prepare = mocker.patch("core.views.prepare_tax_context")
        # Run.
        context = view.get_context_data()
        # Check.
        assert context == mocked_prepare.return_value
        # Check.
        assert mocked_prepare.call_args_list[0][0][0].get("view") == view
        assert isinstance(
            mocked_prepare.call_args_list[0][0][0].get("form"), ExportForm
        )
        assert mocked_prepare.call_args_list[0][0][0].get("analysis_tax") == {
            "errors": 2,
            "locked": [TEST_ADDRESS, TEST_ADDRESS2],
        }
        assert mocked_prepare.call_args_list[0][0][1] == TEST_BUNDLE

    # # get_form
    def test_core_views_exportview_get_form_for_tax_report(self):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        view._tax_data = {"tax_report": "tax_report"}
        # Run.
        form = view.get_form()
        # Check.
        assert isinstance(form, ExportDownloadForm)

    def test_core_views_exportview_get_form_functionality(self):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_ADDRESS)
        # Run.
        form = view.get_form()
        # Check.
        assert isinstance(form, ExportForm)

    # # get_success_url
    def test_core_views_exportview_get_success_url_for_typ_refresh(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        # Run.
        mocked_bundle = mocker.patch("core.views.check_bundle_addresses")
        mocked_process = mocker.patch("core.views.start_export")
        view_object = view.get_success_url(typ="refresh")
        # Check.
        assert view_object == f"/export/{TEST_BUNDLE}/"
        mocked_bundle.assert_not_called()
        mocked_process.assert_not_called()

    def test_core_views_exportview_get_success_url_for_typ_download(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        tax_report = "tax_report"
        view._tax_data = {"tax_report": tax_report}
        # Run.
        mocked_bundle = mocker.patch("core.views.check_bundle_addresses")
        mocked_process = mocker.patch("core.views.start_export")
        view_object = view.get_success_url(typ="download")
        # Check.
        assert view_object == f"/export/download?report={tax_report}"
        mocked_bundle.assert_not_called()
        mocked_process.assert_not_called()

    def test_core_views_exportview_get_success_url_for_empty_addresses(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        # Run.
        mocked_bundle = mocker.patch(
            "core.views.check_bundle_addresses", return_value=""
        )
        mocked_process = mocker.patch("core.views.start_export")
        view_object = view.get_success_url(typ="process")
        # Check.
        assert view_object.status_code == 302
        assert view_object.url == "/"
        mocked_bundle.assert_called_once_with(TEST_BUNDLE)
        mocked_process.assert_not_called()

    def test_core_views_exportview_get_success_url_returns_url_from_address(
        self, mocker
    ):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_ADDRESS)
        # Run.
        mocked_bundle = mocker.patch("core.views.check_bundle_addresses")
        mocked_process = mocker.patch("core.views.start_export")
        view_object = view.get_success_url(typ="process")
        # Check.
        assert view_object == f"/export/{TEST_ADDRESS}/"
        mocked_process.assert_called_once_with(TEST_ADDRESS, TEST_ADDRESS, self.request)
        mocked_bundle.assert_not_called()

    def test_core_views_exportview_get_success_url_returns_url_from_bundle(
        self, mocker
    ):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE)
        # Run.
        addresses = mocker.MagicMock()
        mocked_bundle = mocker.patch(
            "core.views.check_bundle_addresses", return_value=addresses
        )
        mocked_process = mocker.patch("core.views.start_export")
        view_object = view.get_success_url(typ="process")
        # Check.
        assert view_object == f"/export/{TEST_BUNDLE}/"
        mocked_bundle.assert_called_once_with(TEST_BUNDLE)
        mocked_process.assert_called_once_with(TEST_BUNDLE, addresses, self.request)

    def test_core_views_exportview_get_success_url_for_provided_kwargs(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_ADDRESS)
        # Run.
        mocked_bundle = mocker.patch("core.views.check_bundle_addresses")
        mocked_process = mocker.patch("core.views.start_export")
        view_object = view.get_success_url(
            typ="process", provider="provider", use_mve=True, non_zero=True
        )
        # Check.
        assert view_object == f"/export/{TEST_ADDRESS}/"
        mocked_process.assert_called_once_with(
            TEST_ADDRESS,
            TEST_ADDRESS,
            self.request,
            provider="provider",
            use_mve=True,
            non_zero=True,
        )
        mocked_bundle.assert_not_called()


class TestTaxAddressPostRefreshView(BasePostRefreshView):
    """Testing class for :class:`core.views.ExportView` post refresh."""

    # # form_invalid
    def test_core_views_exportview_post_refresh_form_invalid_for_refresh(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE.lower())
        # Run.
        form = mocker.MagicMock()
        mocked_delete = mocker.patch("core.views.reset_export")
        mocked_success = mocker.patch("core.views.ExportView.get_success_url")
        mocked_response = mocker.patch("core.views.HttpResponseRedirect")
        view_object = view.form_invalid(form)
        # Check.
        assert view_object == mocked_response.return_value
        mocked_delete.assert_called_once_with(TEST_BUNDLE)
        mocked_success.assert_called_once_with(typ="refresh")
        mocked_response.assert_called_once_with(mocked_success.return_value)

    # # form_valid
    def test_core_views_exportview_post_refresh_form_valid_for_refresh(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE.lower())
        # Run.
        form = mocker.MagicMock()
        mocked_delete = mocker.patch("core.views.reset_export")
        mocked_success = mocker.patch("core.views.ExportView.get_success_url")
        mocked_response = mocker.patch("core.views.HttpResponseRedirect")
        view_object = view.form_valid(form)
        # Check.
        assert view_object == mocked_response.return_value
        mocked_delete.assert_called_once_with(TEST_BUNDLE)
        mocked_success.assert_called_once_with(typ="refresh")
        mocked_response.assert_called_once_with(mocked_success.return_value)


class TestTaxAddressPostDownloadView(BasePostDownloadView):
    """Testing class for :class:`core.views.ExportView` post download."""

    # # form_valid
    def test_core_views_exportview_post_download_form_valid_for_refresh(self, mocker):
        # Setup view
        view = ExportView()
        view = self.setup_view(view, self.request, TEST_BUNDLE.lower())
        # Run.
        form = mocker.MagicMock()
        mocked_delete = mocker.patch("core.views.reset_export")
        mocked_success = mocker.patch("core.views.ExportView.get_success_url")
        mocked_response = mocker.patch("core.views.HttpResponseRedirect")
        view_object = view.form_valid(form)
        # Check.
        assert view_object == mocked_response.return_value
        mocked_success.assert_called_once_with(typ="download")
        mocked_response.assert_called_once_with(mocked_success.return_value)
        mocked_delete.assert_not_called()


class TestExportDownload(BaseView):
    """Testing class for `export_download`."""

    def test_core_views_export_download_for_no_report(self, mocker):
        self.request.GET = {}
        mocked_response = mocker.patch("core.views.HttpResponse")
        with pytest.raises(Http404):
            with mock.patch("core.views.download_export") as mocked_export:
                export_download(self.request)
        mocked_export.assert_not_called()
        mocked_response.assert_not_called()

    def test_core_views_export_download_for_wrong_report(self):
        self.request.GET = {"report": "1_2_3_4"}
        with mock.patch("core.views.download_export") as mocked_export:
            response = export_download(self.request)
            assert response.status_code == 302
            assert response.url == "/"
        mocked_export.assert_not_called()

    def test_core_views_export_download_for_backend_error(self):
        url_value = "foobar"
        self.request.GET = {"report": f"foo_bar_{url_value}"}
        with mock.patch(
            "core.views.download_export", side_effect=BackendError("")
        ) as mocked_export:
            response = export_download(self.request)
            assert response.status_code == 302
            assert response.url == "/"
        mocked_export.assert_called_once_with(url_value)

    def test_core_views_export_download_for_zip_found(self, mocker):
        url_value = "foobar"
        self.request.GET = {
            "report": f"foo_bar_{url_value}",
            "tax_report": "tax_report",
        }
        content = mocker.MagicMock()
        mocked_response = mocker.patch("core.views.HttpResponse")
        with (
            mock.patch(
                "core.views.download_export", return_value=content
            ) as mocked_export,
        ):
            response = export_download(self.request)
            assert response == mocked_response.return_value
            mocked_export.assert_called_once_with("foobar")
        mocked_response.assert_called_once_with(content, content_type="application/zip")


# # USERS
class TestBundleNameAddDisplayView:
    """Testing class for :class:`core.views.BundleNameAddDisplay`."""

    # # BundleNameAddDisplay
    def test_core_views_bundlenameadddisplay_issubclass_of_detailview(self):
        assert issubclass(BundleNameAddDisplay, DetailView)

    def test_core_views_bundlenameadddisplay_sets_template_name(self):
        assert BundleNameAddDisplay.template_name == "bundlename_add.html"

    def test_core_views_bundlenameadddisplay_sets_model_to_profile(self):
        assert BundleNameAddDisplay.model == Profile


class TestDbBundleNameAddDisplayView(BaseUserCreatedView):
    """Testing class for :class:`core.views.BundleNameAddDisplay`."""

    @pytest.mark.django_db
    def test_core_views_bundlenameadddisplay_get_object_sets_profile_of_user_home(self):
        # Setup view
        view = BundleNameAddDisplay()
        view = self.setup_view(view, self.request)

        # Run.
        view_object = view.get_object()

        # Check.
        assert view_object == self.request.user.profile


class TestBundleNameCreateView:
    """Testing class for :class:`core.views.BundleNameCreate`."""

    # # BundleNameCreate
    def test_core_views_bundlenamecreate_issubclass_of_createview(self):
        assert issubclass(BundleNameCreate, CreateView)

    def test_core_views_bundlenamecreate_issubclass_of_singleobjectmixin(self):
        assert issubclass(BundleNameCreate, SingleObjectMixin)

    def test_core_views_bundlenamecreate_sets_template_name(self):
        assert BundleNameCreate.template_name == "bundlename_add.html"

    def test_core_views_bundlenamecreate_sets_model_to_profile(self):
        assert BundleNameCreate.model == Profile

    def test_core_views_bundlenamecreate_sets_form_class(self):
        assert BundleNameCreate.form_class == ProfileBundleNameForm


class TestDbBundleNameCreateView(BaseUserCreatedView):
    """Testing class for :class:`core.views.BundleNameCreate`."""

    @pytest.mark.django_db
    def test_core_views_bundlenamecreate_get_form_returns_profilebundlenameform(self):
        # Setup view
        view = BundleNameCreate()
        view = self.setup_view(view, self.request)
        # view.object = self.user.profile

        # Run.
        view_form = view.get_form()

        # Check.
        assert isinstance(view_form, ProfileBundleNameForm)
        assert view_form.instance.profile == self.user.profile

    @pytest.mark.django_db
    def test_core_views_bundlenamecreate_get_success_url_returns_bundlename_edit(self):
        # Setup view
        view = BundleNameCreate()
        view = self.setup_view(view, self.request)
        view.object = self.user.profile

        # Run.
        url = view.get_success_url()

        # Check.
        assert url == reverse("bundlename_edit", args=[view.object.name])


class TestBundleNameAddViewView:
    """Testing class for :class:`core.views.BundleNameAddView`."""

    # # BundleNameAddView
    def test_core_views_bundlenameaddview_issubclass_of_canaddbundlenamemixin(self):
        assert issubclass(BundleNameAddView, CanAddBundleNameMixin)

    def test_core_views_bundlenameaddview_issubclass_of_view(self):
        assert issubclass(BundleNameAddView, View)


@pytest.mark.django_db
class TestDbBundleNameAddViewView(BaseUserCreatedView):
    def test_core_views_bundlenameaddview_get_instantiates_bundlenameadddisplay_view(
        self,
    ):
        # Setup view
        view = BundleNameAddView()
        view = self.setup_view(view, self.request)

        # Run.
        view_method = view.get(self.request)

        # Check.
        assert isinstance(view_method.context_data["view"], BundleNameAddDisplay)

    def test_core_views_bundlenameaddview_post_instantiates_bundlenamecreate_view(self):
        # Setup view
        view = BundleNameAddView()
        data = (
            {
                "name": "some name 1",
                "addresses": f"{TEST_ADDRESS} {TEST_ADDRESS2}",
            },
        )
        view = self.setup_view(view, self.request)
        # Run.
        view_method = view.post(
            self.request,
            form=ProfileBundleNameForm(for_profile=self.user.profile, data=data),
        )
        # Check.
        assert isinstance(view_method.context_data["view"], BundleNameCreate)


class TestBundleNameDisplayView:
    """Testing class for :class:`core.views.BundleNameDisplay`."""

    # # BundleNameDisplay
    def test_core_views_bundlenamedisplay_issubclass_of_detailview(self):
        assert issubclass(BundleNameDisplay, DetailView)

    def test_core_views_bundlenamedisplay_sets_template_name(self):
        assert BundleNameDisplay.template_name == "bundlename_edit.html"

    def test_core_views_bundlenamedisplay_sets_model_to_bundlename(self):
        assert BundleNameDisplay.model == BundleName


class TestDbBundleNameDisplayView(BaseUserCreatedView):
    """Testing class for :class:`core.views.BundleNameDisplay`."""

    @pytest.mark.django_db
    def test_core_views_bundlenamedisplay_get_object_sets_object_from_bundlename(
        self,
    ):
        # Setup view
        view = BundleNameDisplay()
        bundlename = self.create_bundlename()
        view = self.setup_view(view, self.request, bundlename.name)

        # Run.
        view_object = view.get_object()

        # Check.
        assert view_object == bundlename

    @pytest.mark.django_db
    def test_core_views_bundlenamedisplay_get_context_data_sets_form(self):
        # Setup view
        view = BundleNameDisplay()
        bundlename = self.create_bundlename()
        view = self.setup_view(view, self.request, bundlename.name)
        view.object = bundlename
        # Run.
        context = view.get_context_data()

        # Check.
        assert isinstance(context["form"], ProfileBundleNameForm)
        assert context["form"].instance.profile == self.user.profile


class TestBundleNameUpdateView:
    """Testing class for :class:`core.views.BundleNameUpdate`."""

    # # BundleNameUpdate
    def test_core_views_bundlenameupdate_issubclass_of_updateview(self):
        assert issubclass(BundleNameUpdate, UpdateView)

    def test_core_views_bundlenameupdate_issubclass_of_singleobjectmixin(self):
        assert issubclass(BundleNameUpdate, SingleObjectMixin)

    def test_core_views_bundlenameupdate_sets_template_name(self):
        assert BundleNameUpdate.template_name == "bundlename_edit.html"

    def test_core_views_bundlenameupdate_sets_model_to_bundlename(self):
        assert BundleNameUpdate.model == BundleName

    def test_core_views_bundlenameupdate_sets_form_class(self):
        assert BundleNameUpdate.form_class == ProfileBundleNameForm


class TestDbBundleNameUpdateView(BaseUserCreatedView):
    """Testing class for :class:`core.views.BundleNameUpdate`."""

    @pytest.mark.django_db
    def test_core_views_bundlenameupdate_get_form_returns_profilebundlenameform(self):
        # Setup view
        view = BundleNameUpdate()
        bundlename = self.create_bundlename()
        view = self.setup_view(view, self.request, bundlename)
        view.object = bundlename

        # Run.
        view_form = view.get_form()

        # Check.
        assert isinstance(view_form, ProfileBundleNameForm)
        assert view_form.instance.profile == self.user.profile

    @pytest.mark.django_db
    def test_core_views_bundlenameupdate_get_object_sets_object_from_profile_bundlename(
        self,
    ):
        # Setup view
        view = BundleNameDisplay()
        bundlename = self.create_bundlename()
        view = self.setup_view(view, self.request, bundlename.name)

        # Run.
        view_object = view.get_object()

        # Check.
        assert view_object == bundlename

    @pytest.mark.django_db
    def test_core_views_bundlenameupdate_get_success_url_returns_bundlename_edit(self):
        # Setup view
        view = BundleNameUpdate()
        bundlename = self.create_bundlename()
        view = self.setup_view(view, self.request, bundlename.name)
        view.object = bundlename

        # Run.
        url = view.get_success_url()

        # Check.
        assert url == reverse("bundlename_edit", args=[view.object.name])


class TestBundleNameEditViewView:
    """Testing class for :class:`core.views.BundleNameEditView`."""

    # # BundleNameEditView

    def test_core_views_bundlenameeditview_issubclass_of_view(self):
        assert issubclass(BundleNameEditView, View)


@pytest.mark.django_db
class TestDbBundleNameEditViewView(BaseUserCreatedView):
    def test_core_views_bundlenameeditview_get_instantiates_bundlenamedisplay_view(
        self,
    ):
        # Setup view
        view = BundleNameEditView()
        bundlename = self.create_bundlename()
        view = self.setup_view(view, self.request, bundlename.name)

        # Run.
        view_method = view.get(self.request, bundlename.name)

        # Check.
        assert isinstance(view_method.context_data["view"], BundleNameDisplay)

    def test_core_views_bundlenameeditview_post_instantiates_bundlenameupdate_view(
        self,
    ):
        # Setup view
        view = BundleNameEditView()
        bundlename = self.create_bundlename()
        view = self.setup_view(view, self.request, bundlename.name)
        data = {
            "name": bundlename.name,
            "addresses": bundlename.addresses,
            "public": bundlename.public,
        }
        # Run.
        view_method = view.post(
            self.request,
            bundlename.name,
            form=ProfileBundleNameForm(for_profile=self.user.profile, data=data),
        )
        # Check.
        assert isinstance(view_method.context_data["view"], BundleNameUpdate)


class TestBundleNameDeleteViewTest:
    """Testing class for :class:`core.views.BundleNameDeleteView`."""

    # # BundleNameDeleteView
    def test_core_views_bundlenamedeleteview_issubclass_of_successmessagemixin(self):
        assert issubclass(BundleNameDeleteView, SuccessMessageMixin)

    def test_core_views_bundlenamedeleteview_issubclass_of_deleteview(self):
        assert issubclass(BundleNameDeleteView, DeleteView)

    def test_core_views_bundlenamedeleteview_sets_template_name(self):
        assert BundleNameDeleteView.template_name == "bundlename_delete.html"

    def test_core_views_bundlenamedeleteview_sets_model_to_bundlename(self):
        assert BundleNameDeleteView.model == BundleName

    def test_core_views_bundlenamedeleteview_sets_success_url(self):
        assert BundleNameDeleteView.success_url == reverse_lazy("home")

    def test_core_views_bundlenamedeleteview_sets_success_message(self):
        assert BundleNameDeleteView.success_message == BUNDLE_NAME_DELETED_MESSAGE


class TestDbBundleNameDeleteViewTest(BaseUserCreatedView):
    @pytest.mark.django_db
    def test_core_views_bundlenamedeleteview_get_object_sets_object_from_bundlename(
        self,
    ):
        # Setup view
        view = BundleNameDeleteView()
        bundlename = self.create_bundlename()
        view = self.setup_view(view, self.request, bundlename.name)

        # Run.
        view_object = view.get_object()

        # Check.
        assert view_object == bundlename


class TestHomePageViewTest:
    """Testing class for :class:`core.views.HomePageView`."""

    # # HomePageView
    def test_core_views_homepageview_issubclass_of_detailview(self):
        assert issubclass(HomePageView, DetailView)

    def test_core_views_homepageview_sets_template_name(self):
        assert HomePageView.template_name == "home.html"

    def test_core_views_homepageview_sets_model_to_profile(self):
        assert HomePageView.model == Profile


class TestDbHomePageViewTest(BaseUserCreatedView):
    @pytest.mark.django_db
    def test_core_views_homepageview_get_object_sets_profile(self):
        # Setup view
        view = HomePageView()
        view = self.setup_view(view, self.request)

        # Run.
        view_object = view.get_object()

        # Check.
        assert view_object == self.request.user.profile


class TestBundleNameView:
    """Testing class for :class:`core.views.BundleNameView`."""

    def test_core_views_bundlenameview_is_subclass_of_canusebundlenamesmixin(self):
        assert issubclass(BundleNameView, CanUseBundleNamesMixin)

    def test_core_views_bundlenameview_is_subclass_of_redirectview(self):
        assert issubclass(BundleNameView, RedirectView)

    def test_core_views_bundlenameview_sets_permanent_class_variable(self):
        assert BundleNameView.permanent is False

    def test_core_views_bundlenameview_sets_pattern_name_class_variable_to_address(
        self,
    ):
        assert BundleNameView.pattern_name == "address"


class TestDbBundleNameView(BaseView):
    """Testing class for :class:`core.views.BundleNameView`."""

    def test_core_views_bundlenameview_dispatch_for_valid_bundle_name_single_address(
        self, mocker
    ):
        # Setup view
        view = BundleNameView()
        addresses = TEST_ADDRESS
        bundlename = mocker.MagicMock()
        bundlename.addresses = addresses
        profile = mocker.MagicMock()
        profile.bundlename_by_name.return_value = bundlename
        user = mocker.MagicMock()
        self.request.user = user
        self.request.user.profile = profile
        mocked_create = mocker.patch("core.views.create_bundle")
        view = self.setup_view(view, self.request)
        name = "name"
        response = view.dispatch(self.request, name)
        # Check.
        assert response.status_code == 302
        assert response.url == f"/{TEST_ADDRESS}"
        mocked_create.assert_not_called()

    def test_core_views_bundlenameview_dispatch_for_valid_bundle_name_multiple_addrs(
        self, mocker
    ):
        # Setup view
        view = BundleNameView()
        addresses = f"{TEST_ADDRESS} {TEST_ADDRESS2}"
        bundlename = mocker.MagicMock()
        bundlename.addresses = addresses
        profile = mocker.MagicMock()
        profile.bundlename_by_name.return_value = bundlename
        user = mocker.MagicMock()
        self.request.user = user
        self.request.user.profile = profile
        bundle = TEST_BUNDLE
        mocked_create = mocker.patch("core.views.create_bundle", return_value=bundle)
        view = self.setup_view(view, self.request)
        name = "name"
        response = view.dispatch(self.request, name)
        # Check.
        assert response.status_code == 302
        assert response.url == f"/{bundle}"
        mocked_create.assert_called_once_with(addresses)

    def test_core_views_bundlenameview_dispatch_for_invalid_bundle_name(self, mocker):
        # Setup view
        view = BundleNameView()
        profile = mocker.MagicMock()
        profile.bundlename_by_name.side_effect = Http404("")
        user = mocker.MagicMock()
        self.request.user = user
        self.request.user.profile = profile
        mocked_create = mocker.patch("core.views.create_bundle")
        view = self.setup_view(view, self.request)
        name = "name"
        with mock.patch("core.views.messages") as mocked_messages:
            response = view.dispatch(self.request, name)
            mocked_messages.error.assert_called_once_with(
                self.request, BUNDLE_NAME_NOT_FOUND_ERROR
            )
        # Check.
        assert response.status_code == 302
        assert response.url == "/home/"
        mocked_create.assert_not_called()

    def test_core_views_bundlenameview_get_redirect_url_for_arg_none(self, mocker):
        # Setup view
        view = BundleNameView()
        user = mocker.MagicMock()
        self.request.user = user
        name = None
        view = self.setup_view(view, self.request)
        mocked_super = mocker.patch("core.views.RedirectView.get_redirect_url")
        with mock.patch("core.views.messages") as mocked_messages:
            response = view.get_redirect_url(name)
            mocked_messages.error.assert_called_once_with(
                self.request, BUNDLE_NAME_NOT_FOUND_ERROR
            )
        mocked_super.assert_not_called()
        # Check.
        assert response == "/home/"

    def test_core_views_bundlenameview_get_redirect_url_functionality(self, mocker):
        # Setup view
        view = BundleNameView()
        user = mocker.MagicMock()
        self.request.user = user
        bundle = "bundle"
        view = self.setup_view(view, self.request)
        mocked_super = mocker.patch("core.views.RedirectView.get_redirect_url")
        response = view.get_redirect_url(bundle)
        mocked_super.assert_called_once_with(bundle)
        # Check.
        assert response == mocked_super.return_value


class TestProfileApiView:
    """Testing class for :class:`core.views.ProfileApiView`."""

    def test_core_views_profileapiview_is_subclass_of_canaccessapimixin(self):
        assert issubclass(ProfileApiView, CanAccessApiMixin)

    def test_core_views_profileapiview_is_subclass_of_templateview(self):
        assert issubclass(ProfileApiView, TemplateView)

    def test_core_views_profileapiview_sets_template_name(self):
        assert ProfileApiView.template_name == "profile_api.html"


class TestDbProfileApiView(BaseView):
    """Testing class for :class:`core.views.ProfileApiView`."""

    def test_core_views_profileapiview_get_context_data_for_refresh(self, mocker):
        view = self.setup_view(ProfileApiView(), self.request)
        self.request.GET = {"refresh": "yes"}
        self.request.user = mocker.MagicMock()
        mocker.patch("core.views.TemplateView.get_context_data", return_value={})
        mocked_token = mocker.patch("core.views.RefreshToken")
        context = view.get_context_data()
        mocked_token.for_user.assert_called_once_with(self.request.user)
        assert context["refresh"] == str(mocked_token.for_user.return_value)
        assert context["access"] == str(mocked_token.for_user.return_value.access_token)

    def test_core_views_profileapiview_get_context_data_without_refresh(self, mocker):
        view = self.setup_view(ProfileApiView(), self.request)
        self.request.GET = {}
        mocker.patch("core.views.TemplateView.get_context_data", return_value={})
        mocked_token = mocker.patch("core.views.RefreshToken")
        context = view.get_context_data()
        assert "refresh" not in context
        mocked_token.for_user.assert_not_called()


class TestProfileAuthorizeView:
    """Testing class for :class:`core.views.ProfileAuthorizeView`."""

    def test_core_views_profileauthorizeview_is_subclass_of_canaccessauthorizemixin(
        self,
    ):
        assert issubclass(ProfileAuthorizeView, CanAccessAuthorizeMixin)

    def test_core_views_profileauthorizeview_is_subclass_of_templateview(self):
        assert issubclass(ProfileAuthorizeView, TemplateView)

    def test_core_views_profileauthorizeview_sets_template_name(self):
        assert ProfileAuthorizeView.template_name == "profile_authorize.html"


@pytest.mark.django_db
class TestDbProfileAuthorizeView(BaseUserCreatedView):

    def test_core_views_profileauthorizeview_get_context_data_sets_wallets(self):
        # Setup view
        view = ProfileAuthorizeView()
        view = self.setup_view(view, self.request)
        # Run.
        view_object = view.get(self.request)
        # Check.
        assert view_object.context_data["wallets"] == ALGORAND_WALLETS


class TestProfileAuthorizeCheckView:
    """Testing class for :class:`core.views.ProfileAuthorizeCheckView`."""

    def test_core_views_profileauthorizecheckview_is_subclass_of_redirectview(self):
        assert issubclass(ProfileAuthorizeCheckView, RedirectView)

    def test_core_views_profileauthorizecheckview_sets_permanent_to_false(self):
        assert ProfileAuthorizeCheckView.permanent is False

    def test_core_views_profileauthorizecheckview_sets_pattern_name_to_profile(self):
        assert ProfileAuthorizeCheckView.pattern_name == "profile"


@pytest.mark.django_db
class TestDbProfileAuthorizeCheckView(BaseUserCreatedView):
    def test_core_views_profileauthorizecheckview_dispatch_for_successful_authorization(
        self, mocker
    ):
        # Setup view
        view = ProfileAuthorizeCheckView()
        view = self.setup_view(view, self.request)
        transaction_id = "transaction_id"
        mocked_update = mocker.patch("core.models.Profile.update_authorized")
        mocked_check = mocker.patch(
            "core.views.check_authorization_transaction",
            return_value=transaction_id,
        )
        with mock.patch("core.views.messages") as mocked_messages:
            response = view.dispatch(self.request)
            mocked_messages.info.assert_called_once_with(
                self.request, AUTHORIZATION_TRANSACTION_CONFIRMED_MESSAGE
            )
        mocked_check.assert_called_once_with(self.request.user.profile)
        mocked_update.assert_called_once_with(transaction_id)
        # Check.
        assert view.pattern_name == "profile"
        assert response.status_code == 302
        assert response.url == "/profile/"

    def test_core_views_profileauthorizecheckview_dispatch_for_no_transaction(
        self, mocker
    ):
        # Setup view
        view = ProfileAuthorizeCheckView()
        view = self.setup_view(view, self.request)
        transaction_id = ""
        mocked_update = mocker.patch("core.models.Profile.update_authorized")
        mocked_check = mocker.patch(
            "core.views.check_authorization_transaction",
            return_value=transaction_id,
        )
        with mock.patch("core.views.messages") as mocked_messages:
            response = view.dispatch(self.request)
            mocked_messages.error.assert_called_once_with(
                self.request, AUTHORIZATION_TRANSACTION_ERROR_MESSAGE
            )
        mocked_check.assert_called_once_with(self.request.user.profile)
        mocked_update.assert_not_called()
        # Check.
        assert view.pattern_name == "profile_authorize"
        assert response.status_code == 302
        assert response.url == "/profile/authorize/"


class TestProfilePermissionFetchView:
    """Testing class for :class:`core.views.ProfilePermissionFetchView`."""

    def test_core_views_profilepermissionfetchview_is_subclass_of_redirectview(self):
        assert issubclass(ProfilePermissionFetchView, RedirectView)

    def test_core_views_profilepermissionfetchview_sets_permanent_to_false(self):
        assert ProfilePermissionFetchView.permanent is False

    def test_core_views_profilepermissionfetchview_sets_pattern_name_to_profile(self):
        assert ProfilePermissionFetchView.pattern_name == "profile"


@pytest.mark.django_db
class TestDbProfilePermissionFetchView(BaseUserCreatedView):
    def test_core_views_profilepermissionfetchview_dispatch_functionality(self, mocker):
        # Setup view
        view = ProfilePermissionFetchView()
        view = self.setup_view(view, self.request)
        mocked_fetch = mocker.patch("core.models.Profile.check_votes_and_permission")
        response = view.dispatch(self.request)
        # Check.
        assert view.pattern_name == "profile"
        assert response.status_code == 302
        assert response.url == "/profile/"
        mocked_fetch.assert_called_once_with()


class TestProfileDisplay:
    """Testing class for :class:`core.views.ProfileDisplay`."""

    def test_core_views_profiledisplay_is_subclass_of_detailview(self):
        assert issubclass(ProfileDisplay, DetailView)

    def test_core_views_profiledisplay_sets_template_name(self):
        assert ProfileDisplay.template_name == "profile.html"

    def test_core_views_profiledisplay_sets_model_to_user(self):
        assert ProfileDisplay.model == User


@pytest.mark.django_db
class TestDbProfileDisplayView(BaseUserCreatedView):
    def test_core_views_profiledisplay_get_returns_both_forms_by_the_context_data(self):
        # Setup view
        view = ProfileDisplay()
        view = self.setup_view(view, self.request)

        # Run.
        view_object = view.get(self.request)

        # Check.
        assert isinstance(view_object.context_data["form"], UpdateUserForm)
        assert isinstance(view_object.context_data["profile_form"], ProfileFormSet)
        assert isinstance(view_object.context_data["form"].instance, user_model)
        assert isinstance(view_object.context_data["profile_form"].instance, user_model)

    def test_core_views_profiledisplay_get_context_data_checks_subscriptions_authorized(
        self, mocker
    ):
        # Setup view
        view = ProfileDisplay()
        view = self.setup_view(view, self.request)

        self.request.user.profile.authorized = "authorized"
        self.request.user.profile.address = TEST_ADDRESS2
        mocked_provider = mocker.patch("core.views.get_permission_provider")
        subscriptions = mocker.MagicMock()
        mocked_provider.return_value.subscriptions.return_value = subscriptions

        # Run.
        view_object = view.get(self.request)

        # Check.
        assert view_object.context_data["subscriptions"] == subscriptions
        mocked_provider.return_value.subscriptions.assert_called_once_with(
            TEST_ADDRESS2
        )

    def test_core_views_profiledisplay_get_context_data_checks_subscriptions_evm_auth(
        self, mocker
    ):
        # Setup view
        view = ProfileDisplay()
        view = self.setup_view(view, self.request)

        self.request.user.profile.authorized = "authorized"
        self.request.user.profile.address = TEST_ADDRESS_EVM
        mocked_provider = mocker.patch("core.views.get_permission_provider")
        subscriptions = mocker.MagicMock()
        mocked_provider.return_value.subscriptions.return_value = subscriptions

        # Run.
        view_object = view.get(self.request)

        # Check.
        assert view_object.context_data["subscriptions"] == subscriptions
        mocked_provider.return_value.subscriptions.assert_called_once_with(
            TEST_ADDRESS_XCHAIN
        )

    def test_core_views_profiledisplay_get_context_data_for_no_subscriptions(
        self, mocker
    ):
        # Setup view
        view = ProfileDisplay()
        view = self.setup_view(view, self.request)

        self.request.user.profile.authorized = "authorized"
        self.request.user.profile.address = TEST_ADDRESS2
        mocked_provider = mocker.patch("core.views.get_permission_provider")
        mocked_provider.return_value.subscriptions.return_value = None

        # Run.
        view_object = view.get(self.request)

        # Check.
        assert view_object.context_data.get("subscriptions") is None
        mocked_provider.assert_called_once_with()
        mocked_provider.return_value.subscriptions.assert_called_once_with(
            TEST_ADDRESS2
        )

    def test_core_views_profiledisplay_get_context_data_checks_subscriptions_no_auth(
        self, mocker
    ):
        # Setup view
        view = ProfileDisplay()
        view = self.setup_view(view, self.request)

        mocked_provider = mocker.patch("core.views.get_permission_provider")

        # Run.
        view_object = view.get(self.request)

        # Check.
        assert view_object.context_data.get("subscriptions") is None
        mocked_provider.assert_not_called()

    def test_core_views_profiledisplay_get_form_fills_form_with_user_data(self):
        # Setup view
        view = ProfileDisplay()
        view = self.setup_view(view, self.request)

        # Run.
        form = view.get_form()

        # Check.
        assert form.data["email"] == self.user.email


class TestProfileUpdate:
    """Testing class for :class:`core.views.ProfileUpdate`."""

    def test_core_views_profileupdate_is_subclass_of_updateview(self):
        assert issubclass(ProfileUpdate, UpdateView)

    def test_core_views_profileupdate_issubclass_of_singleobjectmixin(self):
        assert issubclass(ProfileUpdate, SingleObjectMixin)

    def test_core_views_profileupdate_sets_template_name(self):
        assert ProfileUpdate.template_name == "profile.html"

    def test_core_views_profileupdate_sets_model_to_user(self):
        assert ProfileUpdate.model == User

    def test_core_views_profileupdate_sets_form_class_to_updateuserform(self):
        assert ProfileUpdate.form_class == UpdateUserForm

    def test_core_views_profileupdate_sets_success_url_to_profile(self):
        assert ProfileUpdate.success_url == reverse_lazy("profile")


@pytest.mark.django_db
class TestDbProfileUpdateView(BaseUserCreatedView):
    def test_core_views_profileupdateview_get_object_sets_user(self):
        # Setup view
        view = ProfileUpdate()
        view = self.setup_view(view, self.request)

        # Run.
        view_object = view.get_object()

        # Check.
        assert view_object == self.user

    def test_core_views_profileupdateview_get_form_returns_updateuserform(self):
        # Setup view
        view = ProfileUpdate()
        view = self.setup_view(view, self.request)
        # view.object = self.user.profile

        # Run.
        view_form = view.get_form()

        # Check.
        assert isinstance(view_form, UpdateUserForm)
        assert view_form.instance == self.user


class TestProfileEditView:
    """Testing class for :class:`core.views.ProfileEditView`."""

    def test_core_views_profileeditview_is_subclass_of_view(self):
        assert issubclass(ProfileEditView, View)


@pytest.mark.django_db
class TestDbProfileEditView(BaseUserCreatedView):
    def test_core_views_profileeditview_get_instantiates_profiledisplay_view(self):
        # Setup view
        view = ProfileEditView()
        view = self.setup_view(view, self.request)

        # Run.
        view_method = view.get(self.request)

        # Check.
        assert isinstance(view_method.context_data["view"], ProfileDisplay)

    def test_core_views_profileeditview_post_instantiates_profileupdate_view(self):
        # Setup view
        view = ProfileEditView()
        data = get_user_edit_fake_post_data(self.user)
        view = self.setup_view(view, self.request)

        # Run.
        # form=form, profile_form=profile_form
        view_method = view.post(
            self.request,
            form=UpdateUserForm(instance=self.user, data=data),
        )
        # Check.
        assert isinstance(view_method.context_data["view"], ProfileUpdate)


class TestProfileAccountView:
    """Testing class for :class:`core.views.ProfileAccountView`."""

    def test_core_views_profileaccountview_is_subclass_of_templateview(self):
        assert issubclass(ProfileAccountView, TemplateView)

    def test_core_views_profileaccountview_sets_template_name(self):
        assert ProfileAccountView.template_name == "profile_account.html"


class TestDeactivateProfileViewTest:
    """Testing class for :class:`core.views.DeactivateProfileView`."""

    # # DeactivateProfileView
    def test_core_views_deactivateprofileview_issubclass_of_formview(self):
        assert issubclass(DeactivateProfileView, FormView)

    def test_core_views_deactivateprofileview_sets_template_name(self):
        assert DeactivateProfileView.template_name == "deactivate_profile.html"

    def test_core_views_deactivateprofileview_sets_form_class_to_deatctivateprofileform(
        self,
    ):
        assert DeactivateProfileView.form_class == DeactivateProfileForm

    def test_core_views_deactivateprofileview_sets_success_url(self):
        assert DeactivateProfileView.success_url == "/accounts/inactive/"


@pytest.mark.django_db
class TestDbDeactivateProfileViewTest(BaseUserCreatedView):
    def test_core_views_deactivateprofileview_form_valid_calls_deactivate_profile_form(
        self, mocker
    ):
        # Setup view
        view = DeactivateProfileView()
        view = self.setup_view(view, self.request)
        # Run.
        form = mocker.MagicMock()
        response = view.form_valid(form)
        # Check.
        assert isinstance(response, HttpResponseRedirect)
        assert response.url == "/accounts/inactive/"
        form.deactivate_profile.assert_called_once_with(self.request)
