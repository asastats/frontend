"""Module containing core app's views."""

import logging
import os
import sys

from algosdk.encoding import is_valid_address
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseServerError,
)
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, DetailView, UpdateView
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import DeleteView, FormView
from redis import BusyLoadingError
from rest_framework_simplejwt.tokens import RefreshToken

from api.client import BackendError, download_export, fetch_price
from api.main import fetch_and_serialize_account
from core.forms import (
    DeactivateProfileForm,
    ProfileBundleNameForm,
    ProfileExplorerForm,
    ProfileFormSet,
    ProfileRouterForm,
    UpdateUserForm,
)
from core.helpers import (
    check_export_status,
    check_forbidden_addresses,
    prepare_tax_context,
    reset_export,
    start_export,
)
from core.models import BundleName, Profile
from core.permission_provider import get_permission_provider
from core.permissions import (
    CanAccessApiMixin,
    CanAccessAuthorizeMixin,
    CanAddBundleNameMixin,
    CanUseBundleNamesMixin,
)
from utils.charts import (
    prepare_base_charts_from_serialized_data,
    prepare_consolidated_charts_from_serialized_data,
)
from utils.constants.core import (
    ALGORAND_WALLETS,
    CACHE_TTL_ADDRESS,
    CACHE_TTL_CUSTOM_ADDRESS,
    CONTENT_TYPES_FOR_EXTENSION,
)
from utils.constants.nameservice import NAME_SERVICE_MULTIPLE
from utils.constants.users import (
    AUTHORIZATION_TRANSACTION_CONFIRMED_MESSAGE,
    AUTHORIZATION_TRANSACTION_ERROR_MESSAGE,
    BUNDLE_NAME_DELETED_MESSAGE,
    BUNDLE_NAME_NOT_FOUND_ERROR,
)
from utils.helpers import (
    check_algorand_address,
    check_bundle_addresses,
    create_bundle,
    load_transparency_reports,
    random_slogan,
    safe_referer,
    weighted_randomized_banner,
)
from utils.userhelpers import check_authorization_transaction
from walletauth.gating import linked_addresses_for_user
from widgethost.registry import (
    swap_client_cfg,
    swap_entry_url,
    swap_holdings_tmpl,
    swap_routers,
)

from .forms import AddressForm, ExportDownloadForm, ExportForm

logger = logging.getLogger(__name__)

CACHE_TTL = getattr(settings, "CACHE_TTL", 60 * 90)


@cache_page(CACHE_TTL)
def assets_file(request, suffix):
    """Helper view to retrieve zip, pdf, jpg, eps, svg and png assets files."""
    path = os.path.join(
        settings.STATIC_ROOT,
        "assets/",
        "{}-{}".format(settings.WEBSITE_SHORT_NAME, suffix),
    )
    try:
        response = HttpResponse(
            open(path, "rb"),
            content_type="{}".format(
                CONTENT_TYPES_FOR_EXTENSION[os.path.splitext(path)[1]]
            ),
        )

    except FileNotFoundError:
        raise Http404

    response["Content-Disposition"] = 'attachment; filename="{}"'.format(
        os.path.basename(path)
    )
    return response


def index_file(request, filename):
    """Return text/plan content_type defined by provided `filename`.

    'robots.txt' file is served this way.
    """
    return render(request, filename, {}, content_type="text/plain")


def html_file(request, filename):
    """Return html content defined by provided `filename`."""
    return render(request, f"static/{filename}")


@cache_page(CACHE_TTL)
def social_icons(request, suffix):
    """Helper view to retrieve social icons files served from our emails."""
    path = os.path.join(settings.STATIC_ROOT, "img/social/", "{}".format(suffix))
    response = HttpResponse(
        open(path, "rb"),
        content_type="{}".format(
            CONTENT_TYPES_FOR_EXTENSION[os.path.splitext(path)[1]]
        ),
    )
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(
        os.path.basename(path)
    )
    return response


# # HANDLERS
def custom_server_error(request, template_name="500.html"):
    """Custom handler for server errors.

    For Redis BusyLoadingError redirect to the error page that refreshes
    after 1 minute, with the target being request.path.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param template_name: server error template page to render
    :type template_name: str
    :var typ: class of the error raised
    :type typ: class
    :var template: rendered template in response
    :type template: object
    :return: :class:`django.http.HttpResponseServerError`
    """
    typ, _, _ = sys.exc_info()
    if typ in (BusyLoadingError, ConnectionError):
        template_name = "500r.html"
        logger.warning(
            "Server error 500 - %s - for path '%s'!" % (str(typ), request.path)
        )
    template = loader.get_template(template_name)
    return HttpResponseServerError(template.render())


@method_decorator(csrf_protect, name="dispatch")
class IndexView(FormView):
    """Root page of the site."""

    template_name = "index.html"
    form_class = AddressForm
    addresses = None

    def form_valid(self, form):
        """Set instance address variable to form's address field value."""
        self.addresses = form.cleaned_data.strip()
        return super().form_valid(form)

    def form_invalid(self, form):
        """Change POST data and return form invalid."""
        non_field_errors = form.errors.get("__all__", [])
        if len(non_field_errors) and NAME_SERVICE_MULTIPLE in non_field_errors[0]:
            address = non_field_errors[0].split(NAME_SERVICE_MULTIPLE)[1]
            post = self.request.POST.copy()
            post["bundle"] = ""
            post["address"] = address
            form = self.form_class(post)
            form.add_error("bundle", address)
        return super().form_invalid(form)

    def get_context_data(self, *args, **kwargs):
        """Update context with a random header text.

        :var context["header"]: header text to render
        :type context["header"]: str
        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        context["header"] = random_slogan()
        context["banner"] = weighted_randomized_banner()
        return context

    def get_success_url(self):
        """Update success url with form's addresses value."""
        if " " in self.addresses:
            bundle = create_bundle(self.addresses)
            return reverse("bundle", args=[bundle])
        return reverse("address", args=[self.addresses])


@method_decorator(cache_page(CACHE_TTL), name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class BaseNameServiceView(RedirectView):
    """Base name service class for redirecting to related address view."""

    permanent = False
    pattern_name = "address"
    suffix = ""

    def dispatch(self, request, *args, **kwargs):
        """Central method responsible for defining redirect based on URL argument.

        :var entry: address or addresses separated by space
        :type entry: str
        """
        entry = check_algorand_address(args[0] + self.suffix)
        if " " in entry:
            entry = create_bundle(entry)
            self.pattern_name = "bundle"
        return super().dispatch(request, entry, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        """Return URL for address/bundle page or index page for error."""
        if self.pattern_name == "bundle" or is_valid_address(args[0]):
            return super().get_redirect_url(args[0], **kwargs)
        return reverse("index")


class AnsView(BaseNameServiceView):
    """ANS name provided in URL redirects to related address view."""

    suffix = "/ans"


class NfdView(BaseNameServiceView):
    """NFD name provided in URL redirects to related address view."""

    suffix = "/nfd"


class NameServiceView(BaseNameServiceView):
    """Name provided in URL redirects to related address view."""

    def dispatch(self, request, *args, **kwargs):
        """Central method responsible for defining redirect based on URL argument.

        :var entry: address or addresses separated by space
        :type entry: str
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except ValidationError:
            pass

        form = AddressForm(self.request.POST, initial={"address": args[0]})
        form.errors["__all__"] = []
        form.add_error("bundle", self.args[0])
        return render(self.request, "index.html", {"form": form})


@method_decorator(csrf_protect, name="dispatch")
class BaseAddressView(TemplateView):
    """View for presenting account data.

    Consumes the API 2.0 serialized payload via
    :func:`api.main.fetch_and_serialize_account` rather than building a
    presentation-shaped context directly. The chart datasets emitted to the
    template are produced by the ``*_from_serialized_data`` helpers in
    :mod:`utils.charts`, so the website and the JSON API share a single
    source of truth (and the API's bundle-level cache).

    Context written by :meth:`get_context_data`:

    - ``banner``, ``finished_tax`` -- unchanged page-level extras.
    - ``account`` -- the API 2.0 serialized payload (see
      :class:`api.serializers.EvaluatedAccountSerializer`).
    - ``address`` *or* ``bundle`` -- the address list, written under the
      key that matches the URL type, mirroring the legacy convention so
      template URL helpers (``export_bundle`` etc.) keep working.
    - ``is_bundle`` -- convenience boolean for template dispatch.
    - ``asachart``, ``nftchart``, ``distchart``, ``ratiochart``,
      ``nftfloorchart`` -- chart datasets in the existing JS-consumed shape.
    - ``colors``, ``nft_colors`` -- color-slot maps emitted alongside charts.
    - ``consolidated`` -- :class:`utils.structs.Consolidated` totals.

    Legacy context keys (``asas``, ``values``, ``nft_values``, ``total``,
    ``online``, ``points``, ``warning``, ``information``) are intentionally
    no longer written; the Phase 2 template rewrite rebinds the snippets
    onto ``account`` directly.
    """

    template_name = "address.html"

    def dispatch(self, request, *args, **kwargs):
        """Validate URL value, resolve any bundle to its address list, stash
        for :meth:`get_context_data`.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var url_value: address or bundle value found in url
        :type url_value: str
        :var addresses: public Algorand addresses separated by spaces
        :type addresses: str
        :return: object
        """
        url_value = self.args[0].upper()
        check_forbidden_addresses(url_value)

        if len(url_value) > 50:
            # Single 58-char address: the URL value *is* the address list.
            self.addresses = url_value
        else:
            # 40-char bundle hash: resolve via cache. An empty result means
            # the hash isn't known to us; bounce to index rather than 500.
            self.addresses = check_bundle_addresses(url_value)
            if self.addresses == "":
                return redirect("index")
            check_forbidden_addresses(self.addresses)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Populate context with the API 2.0 serialized payload plus charts.

        :var context: object containing all the data needed for rendering
        :type context: dict
        :var url_value: address or bundle value found in url (length-based
            discriminator between single-address and bundle)
        :type url_value: str
        :var account: API 2.0 serialized payload
        :type account: dict
        :var address_list: parsed list of addresses (one for single-address
            views, multiple for bundles)
        :type address_list: list
        :var is_bundle: True if this view renders multiple addresses
        :type is_bundle: bool
        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        url_value = self.args[0].upper()

        # Page-level extras (unchanged from legacy view).
        if check_export_status(url_value).get("finished_tax") is False:
            context["finished_tax"] = True
        context["banner"] = weighted_randomized_banner()
        context["url_value"] = url_value

        # Heavy lifting: pull the serialized payload through the API cache.
        # On miss this still runs the full prepare_context/fetch_account
        # pipeline (via api.main); on hit it returns the cached dict.
        context["account"] = fetch_and_serialize_account(url_value, self.addresses)

        # Address list for template URL helpers. We keep the legacy key
        # naming (``address`` vs ``bundle``) so existing URL reverses like
        # ``{% url 'export_bundle' bundle|bundle_hash %}`` continue to resolve
        # without template changes in Phase 1.
        address_list = self.addresses.split(" ")
        is_bundle = len(address_list) > 1
        context["bundle" if is_bundle else "address"] = address_list
        context["is_bundle"] = is_bundle

        # Charts: built from the same serialized payload. The emitted
        # JSON-script shapes match what address.js already consumes.
        (
            context["asachart"],
            context["nftchart"],
            context["colors"],
            context["nft_colors"],
        ) = prepare_base_charts_from_serialized_data(context["account"])

        (
            context["distchart"],
            context["ratiochart"],
            context["nftfloorchart"],
            context["consolidated"],
        ) = prepare_consolidated_charts_from_serialized_data(
            context["account"], context["nft_colors"]
        )

        return context


@method_decorator(cache_page(CACHE_TTL_ADDRESS), name="dispatch")
class AddressView(BaseAddressView):
    """Addresses calls"""


@method_decorator(cache_page(CACHE_TTL_CUSTOM_ADDRESS), name="dispatch")
class AddressViewCustom(BaseAddressView):
    """Custom addresses caching calls"""


@method_decorator(cache_page(CACHE_TTL), name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class BaseStaticPageView(TemplateView):
    """Base view for presenting static pages."""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if bool(self.request.GET.get("dark")):
            context["mode"] = "dark"
        return context


class AboutView(BaseStaticPageView):
    """View for presenting About page."""

    template_name = "about.html"


class DisclaimerView(BaseStaticPageView):
    """View for presenting Disclaimer page."""

    template_name = "disclaimer.html"


class FaqView(BaseStaticPageView):
    """View for presenting FAQ page."""

    template_name = "faq.html"


class FeaturesView(BaseStaticPageView):
    """View for presenting Features page."""

    template_name = "features.html"


class SubscriptionsView(BaseStaticPageView):
    """View for presenting Subscriptions page."""

    template_name = "subscriptions.html"


@method_decorator(csrf_protect, name="dispatch")
class TokenomicsView(TemplateView):
    """View for presenting tokenomics page."""

    template_name = "tokenomics.html"

    def get_context_data(self, *args, **kwargs):
        """Update context with the ASASTATS price per 1 ALGO.

        :var context["price"]: ASA Stats Token amount per ALGO
        :type context["price"]: float
        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        context["price"] = fetch_price()
        if bool(self.request.GET.get("dark")):
            context["mode"] = "dark"

        context["transparency_reports"] = load_transparency_reports()
        return context


class ASMPrivacyView(BaseStaticPageView):
    """View for presenting ASA Stats Mobile Privacy Policy Page."""

    template_name = "asm-privacy.html"


# # TAX
@method_decorator(csrf_protect, name="dispatch")
class ExportView(FormView):
    """View for creating ready to import CSV files for account(s)."""

    template_name = "export.html"
    _tax_data = {}

    def dispatch(self, request, *args, **kwargs):
        """Retrieve address(es) from URL value to create report(s) for.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :var url_value: address or bundle value found in url
        :type url_value: str
        :var addresses: public Algorand addresses separated by spaces
        :type addresses: str
        :return: object
        """
        url_value = self.args[0].upper()

        if len(url_value) < 51:
            addresses = check_bundle_addresses(url_value)
            if addresses == "":
                return redirect("index")

            bundle = create_bundle(addresses)
            if bundle != url_value:
                return redirect("export_bundle", bundle)

        self._tax_data = check_export_status(url_value)
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        """Show errors or redirect to success url if user wants refreshed data.

        :param form: object containing all the data needed for rendering
        :type form: :class:ExportForm` or :class:ExportDownloadForm`
        :return: :class:˙HttpResponseRedirect`
        """
        if self.request.POST.get("refresh"):
            reset_export(self.args[0].upper())
            return HttpResponseRedirect(self.get_success_url(typ="refresh"))

        return super().form_invalid(form)

    def form_valid(self, form):
        """Redirect to success url after provided form is validated.

        :param form: object containing all the data needed for rendering
        :type form: :class:ExportForm` or :class:ExportDownloadForm`
        :var typ: unique identifer of the action type
        :type typ: str
        :return: :class:˙HttpResponseRedirect`
        """
        typ = "process"
        if self.request.POST.get("refresh"):
            typ = "refresh"
            reset_export(self.args[0].upper())

        elif self.request.POST.get("download"):
            typ = "download"

        return HttpResponseRedirect(self.get_success_url(typ=typ, **form.cleaned_data))

    def get_context_data(self, *args, **kwargs):
        """Update context with the address from request's GET object.

        :var context: object containing all the data needed for rendering
        :type context: dict
        :var url_value: address or bundle value found in url
        :type url_value: str
        :var analysis_data: collection of data used for analysis purpose
        :type analysis_data: dict
        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        url_value = self.args[0].upper()

        if self._tax_data.get("tax_report"):
            context["finished_tax"] = self._tax_data.get("tax_report")

        if self._tax_data.get("processing_tax"):
            context["processing_tax"] = url_value

        if self._tax_data.get("analysis_tax"):
            analysis_data = self._tax_data.get("analysis_tax", {})
            context["analysis_tax"] = {
                key: value for key, value in analysis_data.items() if value
            }

        return prepare_tax_context(context, url_value)

    def get_form(self, *args, **kwargs):
        """Return form instance used to render tax page.

        :var form_class: form class which view uses
        :type form_class: :class:`ExportForm` or :class:`ExportDownloadForm`
        :var url_value: address or bundle value found in url
        :type url_value: str
        :return: object
        """
        form_class = ExportForm
        if self._tax_data.get("tax_report"):
            form_class = ExportDownloadForm

        return super().get_form(*args, form_class=form_class, **kwargs)

    def get_success_url(self, typ, **kwargs):
        """Call adresses processing background task after successful form validation.

        :param typ: unique identifer of the action type
        :type typ: str
        :var url_value: address or bundle value found in url
        :type url_value: str
        :var url_name: Django engine's unique URL name/identifier
        :type url_name: str
        :var addresses: public Algorand addresses separated by spaces
        :type addresses: str
        :return: str
        """
        url_value = self.args[0].upper()
        url_name = "export_bundle" if len(url_value) < 51 else "export_address"

        if typ == "refresh":
            return reverse(url_name, args=[url_value])

        elif typ == "download":
            return (
                reverse("export_download").rstrip("/")
                + "?report="
                + self._tax_data.get("tax_report")
            )

        addresses = (
            check_bundle_addresses(url_value) if len(url_value) < 51 else url_value
        )
        if addresses == "":
            return redirect("index")

        start_export(url_value, addresses, self.request, **kwargs)

        return reverse(url_name, args=[url_value])


def export_download(request, **kwargs):
    """Helper view for downloading of compressed CSV files holding export data.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :var report: zipped report file name stem
    :type report: str
    :var splitted: report's specifications collection found in file name
    :type splitted: list
    :var url_value: address or bundle value found in file name
    :type url_value: str
    :var content: compressed report's content
    :type content: bytes
    :var response: Django response holding the compressed report
    :type response: :class:`django.http.HttpResponse`
    :return: :class:`django.http.HttpResponse`
    """
    report = request.GET.get("report", "")
    if not report:
        raise Http404

    splitted = report.split("_")
    if len(splitted) != 3:
        return redirect("index")

    url_value = splitted[-1]
    try:
        content = download_export(url_value)

    except BackendError as exc:
        logger.warning("export download failed for %s: %s", url_value, exc)
        return redirect("index")

    response = HttpResponse(content, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{report}.zip"'
    return response


# # USERS
class BundleNameAddDisplay(DetailView):
    """Display add new bundle name page.

    Django generic CBV DetailView needs template and model to be declared,
    together with get_object method. :class:`BundleNameAddView` is the main
    class for adding bundle name process and it uses this class as
    GET part of the process.
    """

    template_name = "bundlename_add.html"
    model = Profile

    def get_object(self, queryset=None):
        """Returns/sets profile object

        Overriding this method is Django DetailView requirement

        :return: profile instance
        """
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        """Update context with bundle name adding form

        :var context["form"]: form for bundle name add
        :type context["form"]: :class:`ProfileBundleNameForm`
        :return: dict
        """
        context = super().get_context_data(**kwargs)
        context["form"] = ProfileBundleNameForm(for_profile=self.object)
        return context


class BundleNameCreate(CreateView, SingleObjectMixin):
    """Create new bundle name.

    Django generic CBV CreateView and SingleObjectMixin needs template,
    model and form_class to be declared,
    :class:`BundleNameAddView` is the main class in adding bundle name process
    and it uses this class as POST part of the process.
    """

    template_name = "bundlename_add.html"
    model = Profile
    form_class = ProfileBundleNameForm

    def get_form(self, form_class=None):
        """Instantiate and return form for creating new bundle name

        Instance's profile is set from request user's instance.
        form_class attribute is used to instantiate form with profile
        from request user's profile.

        :return: :class:`Form`
        """
        self.object = self.request.user.profile
        return self.form_class(for_profile=self.object, data=self.request.POST)

    def get_success_url(self):
        """Return url to redirect to after successful update.

        Use created bundle name for url lookup.

        :return: str
        """
        return reverse("bundlename_edit", args=[self.object.name])


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class BundleNameAddView(CanAddBundleNameMixin, View):
    """Add new bundle name to profile.

    It uses :class:`BundleNameAddDisplay` as GET proxy and :class:`BundleNameCreate`
    as POST proxy to accomplish complete adding bundle name process through
    a single bundle name.
    """

    def get(self, request, *args, **kwargs):
        """Sets :class:`BundleNameAddDisplay` get method as its own GET

        :return: :class:`BundleNameAddDisplay` as_view method
        """
        view = BundleNameAddDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Sets :class:`BundleNameCreate` post method as its own POST

        :return: :class:`BundleNameCreate` as_view method
        """
        view = BundleNameCreate.as_view()
        return view(request, *args, **kwargs)


class BundleNameDisplay(DetailView):
    """Display bundle name data.

    Django generic CBV DetailView needs template and model to be declared,
    together with get_object method. :class:`BundleNameEditView` is the main
    class for viewing and updating bundle name data and it uses this class as
    GET part of the process.
    """

    template_name = "bundlename_edit.html"
    model = BundleName

    def get_object(self, queryset=None):
        """Return/set bundle name object.

        Overriding this method is Django DetailView requirement.
        BundleName object is get by unique bundle name id provided by url/args.

        :var bundle_name: unique bundle name
        :type bundle_name: str
        :return: :class:`BundleName`
        """
        bundle_name = self.args[0]
        return self.request.user.profile.bundlename_by_name(bundle_name)

    def get_context_data(self, **kwargs):
        """Update context with bundle name updating form.

        :var context["form"]: form for bundle name update
        :type context["form"]: :class:`ProfileBundleNameForm`
        :return: dict
        """
        context = super().get_context_data(**kwargs)
        data = {
            "name": self.object.name,
            "addresses": self.object.addresses,
            "public": self.object.public,
        }
        context["form"] = ProfileBundleNameForm(
            for_profile=self.request.user.profile, initial=data
        )
        return context


class BundleNameUpdate(UpdateView, SingleObjectMixin):
    """Update bundle name data.

    Django generic CBV UpdateView and SingleObjectMixin needs template,
    model, form_class to be declared, :class:`BundleNameEditView` is the main
    class in updating bundle name data process and it uses this class as the
    POST part of the process.
    """

    template_name = "bundlename_edit.html"
    model = BundleName
    form_class = ProfileBundleNameForm

    def get_form(self, form_class=None):
        """Instantiates and returns form for updating bundle name data.

        Instance's `form_class` attribute is used to instantiate
        form with instance set to bundle name object and profile to
        request user's profile

        :return: instance of bundle name adding form
        """
        return self.form_class(
            instance=self.object,
            for_profile=self.request.user.profile,
            data=self.request.POST,
        )

    def get_object(self, queryset=None):
        """Returns/sets bundle name object

        Overriding this method is Django UpdateView requirement. Object is
        get by name from url arguments.

        :var bundle_name: unique bundle name
        :type bundle_name: str
        :return: bundle name instance
        """
        bundle_name = self.args[0]
        return self.request.user.profile.bundlename_by_name(bundle_name)

    def get_success_url(self):
        """Returns url to redirect to after successful update

        It uses initial args for url lookup

        :return: updating bundle name edit page url
        """
        return reverse("bundlename_edit", args=[self.object.name])


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class BundleNameEditView(View):
    """Display and update bundle name data

    It uses :class:`BundleNameDisplay` as GET proxy and :class:`BundleNameUpdate`
    as POST proxy to accomplish updating bundle name process through a
    single bundle name.
    """

    def get(self, request, *args, **kwargs):
        """Sets :class:`BundleNameDisplay` get method as its own GET

        :return: :class:`BundleNameDisplay` as_view method
        """
        view = BundleNameDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Sets :class:`BundleNameUpdate` post method as its own POST

        :return: :class:`BundleNameUpdate` as_view method
        """
        view = BundleNameUpdate.as_view()
        return view(request, *args, **kwargs)


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class BundleNameDeleteView(SuccessMessageMixin, DeleteView):
    """Delete bundle name from database.

    Django generic CBV DeleteView needs template, model and success_url to be declared.
    together with get_object method.
    """

    template_name = "bundlename_delete.html"
    model = BundleName
    success_url = reverse_lazy("home")
    success_message = BUNDLE_NAME_DELETED_MESSAGE

    def get_object(self, queryset=None):
        """Return/set bundle name object.

        Overriding this method is Django DetailView requirement.
        Bundle name object is get by unique bundle name provided by url/args.

        :var name: unique bundle name
        :type name: str
        :return: :class:`BundleName`
        """
        bundle_name = self.args[0]
        return self.request.user.profile.bundlename_by_name(bundle_name)


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class HomePageView(DetailView):
    """Main view for user/profile home page

    Django generic CBV DetailView needs template and model to be declared,
    together with get_object method
    """

    template_name = "home.html"
    model = Profile

    def get_object(self):
        """Returns/sets profile object

        Overriding this method is Django DetailView requirement

        :return: profile instance
        """
        return self.request.user.profile


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class BundleNameView(CanUseBundleNamesMixin, RedirectView):
    """Class for redirecting to bundle page."""

    permanent = False
    pattern_name = "address"

    def dispatch(self, request, *args, **kwargs):
        """Central method responsible for defining redirect based on URL argument.

        :var entry: address or addresses separated by space
        :type entry: str
        """
        entry = None
        try:
            entry = self.request.user.profile.bundlename_by_name(args[0]).addresses
            if " " in entry:
                entry = create_bundle(entry)
                self.pattern_name = "bundle"

        except Http404:
            pass

        return super().dispatch(request, entry, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        """Return URL for address/bundle page for bundle name."""
        if args[0] is None:
            messages.error(self.request, BUNDLE_NAME_NOT_FOUND_ERROR)
            return reverse("home")

        return super().get_redirect_url(args[0], **kwargs)


# # PROFILE
@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class ProfileApiView(CanAccessApiMixin, TemplateView):
    """View user's API access related data."""

    template_name = "profile_api.html"

    def get_context_data(self, *args, **kwargs):
        """Update context with the address from request's GET object.

        :var context: object containing all the data needed for rendering
        :type context: dict
        :var refresh: URL query refresh value
        :type refresh: str
        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        refresh = self.request.GET.get("refresh", "")
        if refresh == "yes":
            refresh_token = RefreshToken.for_user(self.request.user)
            context["refresh"] = str(refresh_token)
            context["access"] = str(refresh_token.access_token)
        return context


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class ProfileSettingsView(View):
    """User settings page: smart-router and preferred-explorer preferences.

    Router options are discovered (manifests with ``category = "swap"``) and
    explorer options come from the explorer registry, so new entries appear
    automatically. The router section records a preference only; the explorer
    section is additionally gated on the Intro subscription tier -- below it the
    template renders the control disabled and a click routes to subscriptions,
    and a forged POST is redirected there too.

    :var template_name: name of the template to render
    :type template_name: str
    """

    template_name = "profile_settings.html"

    def _context(self, request):
        """Return the base context with both preference forms bound to profile.

        :param request: current request
        :type request: :class:`HttpRequest`
        :return: dict
        """
        profile = request.user.profile
        return {
            "form": ProfileRouterForm(instance=profile),
            "explorer_form": ProfileExplorerForm(instance=profile),
            "can_access_explorer": profile.can_access_explorer_setting(),
        }

    def get(self, request, *args, **kwargs):
        """Render the preference forms bound to the current profile.

        :return: :class:`HttpResponse`
        """
        return render(request, self.template_name, self._context(request))

    def post(self, request, *args, **kwargs):
        """Persist the submitted section and redirect back (post/redirect/get).

        The ``section`` field selects which form is processed. The explorer
        section requires Intro permission; an unentitled submission is sent to
        the subscriptions page rather than saved.

        :return: :class:`HttpResponse`
        """
        profile = request.user.profile
        section = request.POST.get("section", "router")

        if section == "explorer":
            if not profile.can_access_explorer_setting():
                return redirect("subscriptions")
            form = ProfileExplorerForm(data=request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(
                    request, "Explorer preference saved.", extra_tags="explorer"
                )
                return redirect("profile_settings")
            context = self._context(request)
            context["explorer_form"] = form
            return render(request, self.template_name, context)

        form = ProfileRouterForm(data=request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Smart router preference saved.", extra_tags="router"
            )
            return redirect("profile_settings")
        context = self._context(request)
        context["form"] = form
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class ProfileAuthorizeView(CanAccessAuthorizeMixin, TemplateView):
    """View for authorization of provided profile address.

    :var template_name: name of the template to render
    :type template_name: str
    """

    template_name = "profile_authorize.html"

    def get_context_data(self, *args, **kwargs):
        """Add the supported wallet list for the connect-a-wallet cards.

        :var context: template context populated by the parent implementation
        :type context: dict
        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        context["wallets"] = ALGORAND_WALLETS
        context["wallet_test_mode"] = settings.WALLET_TEST_MODE
        return context


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class ProfileAuthorizeCheckView(RedirectView):
    """View for checking authorization transaction of provided profile address."""

    permanent = False
    pattern_name = "profile"

    def dispatch(self, request, *args, **kwargs):
        """Central method responsible for defining redirect based on URL argument.

        :var entry: address or addresses separated by space
        :type entry: str
        """
        transaction_id = check_authorization_transaction(self.request.user.profile)
        if transaction_id:
            self.request.user.profile.update_authorized(transaction_id)
            messages.info(self.request, AUTHORIZATION_TRANSACTION_CONFIRMED_MESSAGE)
        else:
            self.pattern_name = "profile_authorize"
            messages.error(self.request, AUTHORIZATION_TRANSACTION_ERROR_MESSAGE)
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class ProfilePermissionFetchView(RedirectView):
    """View for votes and permission values fetch for profile."""

    permanent = False
    pattern_name = "profile"

    def dispatch(self, request, *args, **kwargs):
        """Central method responsible for calling the permission fetching routine."""
        self.request.user.profile.check_votes_and_permission()
        return super().dispatch(request, *args, **kwargs)


class ProfileDisplay(DetailView):
    """Displays user's profile page

    Django generic CBV DetailView needs template and model to be declared.

    :class:`ProfileEditView` is the main class for viewing and updating
    user/prodfile data and it uses this class as GET part of the process.
    """

    template_name = "profile.html"
    model = User

    def get(self, request, *args, **kwargs):
        """Handles GET requests and instantiates blank versions of the form

        and its inline formset. User editing form is get by class' get_form
        method and profile editing formset is instantiated here.
        """
        self.object = None
        form = self.get_form()
        profile_form = ProfileFormSet(instance=self.request.user)
        return self.render_to_response(
            self.get_context_data(form=form, profile_form=profile_form)
        )

    def get_context_data(self, *args, **kwargs):
        """Update context with profile's subscription tier values.

        :var context["header"]: header text to render
        :type context["header"]: str
        :var context["subscriptions"]: collection of tier links and expiration messages
        :type context["subscriptions"]: dict
        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.profile.authorized:
            subscriptions = get_permission_provider().subscriptions(
                self.request.user.profile.algorand_address
            )
            if subscriptions:
                context["subscriptions"] = subscriptions
        return context

    def get_form(self, form_class=None):
        """Instantiates and returns form for updating profile data

        :class:`UpdateUserForm` is used to instantiate form with instance set
        to user object and form's data from the same object

        :return: instance of profile editing form
        """
        self.object = self.request.user
        data = {
            "first_name": self.object.first_name,
            "last_name": self.object.last_name,
            "email": self.object.email,
        }
        return UpdateUserForm(instance=self.object, data=data)


class ProfileUpdate(UpdateView, SingleObjectMixin):
    """Updates user/profile`data

    Django generic CBV UpdateView and SingleObjectMixin needs template,
    model and form_class to be declared, :class:`ProfileEditView` is the main
    class in updating profile data process and it uses this class as the
    POST part of the process.
    """

    template_name = "profile.html"
    model = User
    form_class = UpdateUserForm
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        """Returns/sets user object

        Overriding this method is Django DetailView requirement

        :return: user instance
        """
        return self.request.user

    def get_form(self, *args, **kwargs):
        """Instantiates and returns form for editing user/profile data

        Instance's user object is the request user's instance and it's used
        by form_class to instantiate form.

        :return: instance of user/profile editing form
        """
        self.object = self.request.user
        return self.form_class(instance=self.object, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance and its inline
        formset with the passed POST variables and then checking them for
        validity.
        """
        self.object = None
        form = self.get_form(request.POST)
        profile_form = ProfileFormSet(instance=self.request.user, data=request.POST)
        if form.is_valid() and profile_form.is_valid():
            return self.form_valid(form, profile_form)
        return self.form_invalid(form, profile_form)

    def form_valid(self, form, profile_form):
        """
        Called if all forms are valid. Updates a User instance along with
        associated Profile and then redirects to a success page.
        """
        self.object = form.save()
        profile_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, profile_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form, profile_form=profile_form)
        )


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class ProfileEditView(View):
    """Update and displays profile data"""

    def get(self, request, *args, **kwargs):
        """Sets :class:`ProfileDisplay` get method as its own GET

        :return: :class:`ProfileDisplay` as_view method
        """
        view = ProfileDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Sets :class:`ProfileUpdate` post method as its own POST

        :return: :class:`ProfileUpdate` as_view method
        """
        view = ProfileUpdate.as_view()
        return view(request, *args, **kwargs)


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class ProfileAccountView(TemplateView):
    """View for presenting profile account page."""

    template_name = "profile_account.html"


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class DeactivateProfileView(FormView):
    """Deactivates current user.

    Current user is logged out and deacrtivated after the form is
    submitted and successful captcha is entered. User is redirected
    to django-allauth inactive account page afterward.
    """

    template_name = "deactivate_profile.html"
    form_class = DeactivateProfileForm
    success_url = "/accounts/inactive/"

    def form_valid(self, form):
        """
        If user has correctly entered captcha value then form's
        deactivate_profile method is called with current
        request object as argument.
        """
        form.deactivate_profile(self.request)
        return super().form_valid(form)


class SwapEntryView(TemplateView):
    """Non-cached htmx partial rendering the swap entry for the user's router.

    The address page is ``cache_page``'d across users, so this per-user entry is
    loaded separately. It links to the user's preferred router's swap page when
    the user has linked at least one address on the page; otherwise nothing.

    :var template_name: relative path to the partial template
    :type template_name: str
    """

    template_name = "_swap_entry.html"

    def get_context_data(self, *args, **kwargs):
        """Resolve the preferred-router swap URL + client cfg for a linked viewer.

        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        context["swap_url"] = ""
        user = self.request.user
        if not user.is_authenticated:
            return context
        value = self.args[0].upper()
        addresses = (
            [value] if len(value) > 50 else check_bundle_addresses(value).split()
        )
        linked = linked_addresses_for_user(user, addresses)
        if linked:
            router = user.profile.preferred_router_or_default()
            cfg = swap_client_cfg(router)
            context["swap_url"] = swap_entry_url(router, value)
            context["swap_router"] = router
            context["swap_network"] = cfg["network"]
            context["swap_router_name"] = dict(swap_routers()).get(router, router)
            context["swap_referrer"] = cfg["referrer"]
            context["swap_fee_bps"] = cfg["fee_bps"]
            context["swap_api_key"] = cfg["api_key"]
            context["swap_holdings_tmpl"] = swap_holdings_tmpl(router)
            context["swap_address"] = sorted(linked)[0]
            # The shared controller is loaded once; the chosen router's SDK bundle
            # is loaded by id, e.g. "haystack/haystack-sdk.bundle.js".
            context["swap_sdk_static"] = f"{router}/{router}-sdk.bundle.js"
        return context


class SwapSourceRedirectView(View):
    """Non-cached: resolve a Swap click for one asset off the cached accordion.

    The address-page accordion is ``cache_page``'d, so its per-asset Swap links
    are user-agnostic and point here. This resolves the per-user linkage gate off
    the cache and:

    * anonymous -> login (with ``next`` back here),
    * linked    -> back to the address page with ``?swap_open=<asset_id>`` so the
      client opens the swap modal (the marker gate then decides enabled vs the
      "not available" state, exactly as for an authenticated inline click),
    * unlinked  -> back to the address page with ``?swap_error=unlinked`` (toast).
    """

    def get(self, request, value, asset_id):
        """Route a Swap click to login, the swap modal, or the unlinked toast.

        :return: HttpResponseRedirect
        """
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        address = value.upper()
        addresses = (
            [address] if len(address) > 50 else check_bundle_addresses(address).split()
        )

        # Calculate referer and separator once upfront to keep it DRY
        referer = safe_referer(request)
        separator = "&" if referer and "?" in referer else "?"

        if not linked_addresses_for_user(request.user, addresses):
            # Not their address: bounce back with a flag the client toasts.
            if referer:
                return redirect(f"{referer}{separator}swap_error=unlinked")
            raise Http404

        # Linked: return to the address page and let the client open the swap
        # modal for this asset (same path as an authenticated inline Swap click).
        if referer:
            return redirect(f"{referer}{separator}swap_open={asset_id}")

        # No safe referer (e.g. a direct hit on this URL): fall back to the
        # standalone router swap page with the asset preselected.
        base = swap_entry_url(
            request.user.profile.preferred_router_or_default(), address
        )
        if not base:
            raise Http404

        return redirect(f"{base}?from={asset_id}")
