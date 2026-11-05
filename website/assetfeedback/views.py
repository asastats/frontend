"""Module containing the asset feedback view. See docs/logbook.md."""

from django.conf import settings
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import Http404
from django.shortcuts import render
from django.utils.crypto import salted_hmac
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from assetfeedback.forms import AssetFeedbackForm
from assetfeedback.models import AssetFeedback
from core.appclient import app_client

MAX_ASSET_ID = 2**63 - 1
MIN_FORM_SECONDS = 3
MAX_FORM_SECONDS = 6 * 3600
HOUR = 3600
DAY = 86400
ANONYMOUS_HOURLY_LIMIT = 10
USER_HOURLY_LIMIT = 30
NAME_LENGTH = 64
MODAL = "assetfeedback/_modal.html"
THANKS = "assetfeedback/_thanks.html"
TOO_FAST = "That was very quick. Please check the form and send it again."
EXPIRED = "This form has expired. Please check it and send it again."
TOO_MANY = "You have sent a lot of reports. Please try again later."

_signer = TimestampSigner(salt="assetfeedback")


def _client_ip(request):
    """Return the client's IP from nginx's header, never `X-Forwarded-For`.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: str
    """
    header = getattr(settings, "ALLAUTH_TRUSTED_CLIENT_IP_HEADER", None)
    if header:
        value = request.META.get(f"HTTP_{header.upper().replace('-', '_')}")
        if value:
            return value
    return request.META.get("REMOTE_ADDR", "")


def _requester(request):
    """Return the hashed identity that throttles use: user id or IP.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: str
    """
    raw = f"u{request.user.pk}" if request.user.is_authenticated else _client_ip(request)
    return salted_hmac("assetfeedback", raw).hexdigest()[:32]


def _context(request, asset_id, form):
    """Return the modal's template context.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param asset_id: Algorand Standard Asset ID
    :type asset_id: int
    :param form: form instance to render
    :type form: :class:`AssetFeedbackForm`
    :return: dict
    """
    return {
        "asset_id": asset_id,
        "form": form,
        "name": (request.GET.get("name") or request.POST.get("name") or "")[:NAME_LENGTH],
        "show_personal": app_client(request) is None,
    }


def _started_error(token, asset_id):
    """Return why the signed form token is unusable, or None.

    :param token: signed form token
    :type token: str
    :param asset_id: Algorand Standard Asset ID
    :type asset_id: int
    :return: str or None
    """
    try:
        if _signer.unsign(token, max_age=MAX_FORM_SECONDS) != str(asset_id):
            return EXPIRED
    except BadSignature:
        return EXPIRED
    try:
        _signer.unsign(token, max_age=MIN_FORM_SECONDS)
    except SignatureExpired:
        return None
    return TOO_FAST


@method_decorator(never_cache, name="dispatch")
class AssetFeedbackView(View):
    """Show and accept the feedback form; pages holding the button are cached."""

    def _form(self, request, asset_id, data=None, require_captcha=False):
        """Return the form and the modal's context for it.

        :return: two-tuple
        """
        form = AssetFeedbackForm(
            data,
            initial={"started": _signer.sign(str(asset_id))},
            show_personal=app_client(request) is None,
            require_captcha=require_captcha,
        )
        return form, _context(request, asset_id, form)

    def get(self, request, asset_id):
        """Return the modal fragment.

        :return: :class:`django.http.HttpResponse`
        """
        if asset_id > MAX_ASSET_ID:
            raise Http404
        _, context = self._form(request, asset_id)
        return render(request, MODAL, context)

    def post(self, request, asset_id):
        """Store a valid report and return the thank-you state.

        :return: :class:`django.http.HttpResponse`
        """
        if asset_id > MAX_ASSET_ID:
            raise Http404

        requester = _requester(request)
        hourly_key = f"assetfeedback:hour:{requester}"
        signed_in = request.user.is_authenticated
        limit = USER_HOURLY_LIMIT if signed_in else ANONYMOUS_HOURLY_LIMIT
        over_limit = cache.get(hourly_key, 0) >= limit
        form, context = self._form(
            request,
            asset_id,
            request.POST,
            require_captcha=over_limit and not signed_in,
        )

        if request.POST.get("website"):
            return render(request, THANKS)

        if over_limit and signed_in:
            form.is_valid()
            form.add_error(None, TOO_MANY)
            return render(request, MODAL, context)

        if not form.is_valid():
            return render(request, MODAL, context)

        error = _started_error(form.cleaned_data["started"], asset_id)
        if error:
            form.add_error(None, error)
            data = request.POST.copy()
            data["started"] = _signer.sign(str(asset_id))
            form.data = data
            return render(request, MODAL, context)

        cache.add(hourly_key, 0, HOUR)
        cache.incr(hourly_key)

        if cache.add(f"assetfeedback:asset:{requester}:{asset_id}", 1, DAY):
            AssetFeedback.objects.create(
                asset_id=asset_id,
                kind=form.cleaned_data["kind"],
                link=form.cleaned_data["link"],
                details=form.cleaned_data["details"],
                contact=form.cleaned_data.get("contact", ""),
                reporter_address=form.cleaned_data.get("reporter_address", ""),
                user=request.user if signed_in else None,
                source=(
                    AssetFeedback.Source.APP
                    if app_client(request)
                    else AssetFeedback.Source.WEB
                ),
            )
        return render(request, THANKS)
