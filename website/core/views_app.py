"""Views the ASA Stats app depends on: Universal Links and App Links documents.

Contracts with mobile/ (entitlements, AndroidManifest.xml); see docs/logbook.md.
"""

from django.conf import settings
from django.http import JsonResponse

#: Bundle id (iOS) and package name (Android) of the store app.
APP_ID = "com.asastats.app"

#: Never opened in the app: sign-in, API, the F4 ticket flow, files, admin.
AASA_EXCLUDED_PATHS = (
    "/accounts/*",
    "/api/*",
    "/app/auth/*",
    "/static/*",
    "/admin/*",
    "/captcha/*",
)


def apple_app_site_association(request):
    """Return the Universal Links document for the app.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: :class:`django.http.JsonResponse`
    """
    components = [{"/": path, "exclude": True} for path in AASA_EXCLUDED_PATHS]
    components.append({"/": "/*"})
    return JsonResponse(
        {
            "applinks": {
                "details": [
                    {
                        "appIDs": [f"{settings.APPLE_APP_ID_PREFIX}.{APP_ID}"],
                        "components": components,
                    }
                ]
            }
        }
    )


def assetlinks(request):
    """Return the Digital Asset Links document that verifies the app's App Links.

    Empty until ``ANDROID_CERT_SHA256`` holds the signing key fingerprints.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: :class:`django.http.JsonResponse`
    """
    if not settings.ANDROID_CERT_SHA256:
        return JsonResponse([], safe=False)

    return JsonResponse(
        [
            {
                "relation": ["delegate_permission/common.handle_all_urls"],
                "target": {
                    "namespace": "android_app",
                    "package_name": APP_ID,
                    "sha256_cert_fingerprints": list(settings.ANDROID_CERT_SHA256),
                },
            }
        ],
        safe=False,
    )
