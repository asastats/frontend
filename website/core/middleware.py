"""Module containing core app's custom middlewares."""

from django.conf import settings
from django_minify_html.middleware import MinifyHtmlMiddleware

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
