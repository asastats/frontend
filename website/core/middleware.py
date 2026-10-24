"""Module containing core app's custom middlewares."""

import re

from django.http import Http404
from django_minify_html.middleware import MinifyHtmlMiddleware

from core.appclient import parse_app_client, widget_hidden
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS


class CustomMinifyHtmlMiddleware(MinifyHtmlMiddleware):
    """Custom configuration for django-minify-html middleware."""

    minify_args = MinifyHtmlMiddleware.minify_args | {
        "minify_css": False,
        "minify_js": False,
        "minify_doctype": False,
        "allow_removing_spaces_between_attributes": False,
        "allow_noncompliant_unquoted_attribute_values": False,
        "keep_closing_tags": True,
    }


class CustomUserHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        header = "user"
        if (
            request.user.is_authenticated
            and request.user.profile
            and request.user.profile.permission
            >= SUBSCRIPTION_TIER_PERMISSIONS.get("Intro")
        ):
            header = "other"

        response["X-User-Header"] = header
        return response


#: Every view of a widget is mounted under its name (widgets/urls.py).
WIDGET_PATH_REGEX = re.compile(r"^/widgets/(?P<name>[\w-]+)/")


class AppClientMiddleware:
    """Set ``request.app_client`` from the ASA Stats app's user-agent token,
    and answer 404 for a widget switched off on the app's platform."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.app_client = parse_app_client(request.META.get("HTTP_USER_AGENT"))
        if request.app_client is not None:
            match = WIDGET_PATH_REGEX.match(request.path_info)
            if match and widget_hidden(request, match.group("name")):
                raise Http404("widget not available in the app")

        return self.get_response(request)
