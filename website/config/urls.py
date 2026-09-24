"""Website URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/3.2/topics/http/urls/

Examples:

Function views::

    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')

Class-based views::

    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')

Including another URLconf::

    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import re

from django.conf import settings  # noqa: F401 - the debug-toolbar block below
from django.contrib.sitemaps.views import sitemap
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import include, path, re_path

from api import urls as api_urls
from core import urls as core_urls
from walletauth import urls as walletauth_urls
from widgets import urls as widget_urls

from .sitemaps import PrioritizedStaticViewSitemap, StaticViewSitemap

sitemaps = {"statichp": PrioritizedStaticViewSitemap, "static": StaticViewSitemap}

#: Assets a browser fetches from the site root on its own, whatever the page.
#:
#: **Django has to answer these, not only nginx.** Production aliases them to
#: `static/` and never reaches Django, but nothing else does - and `core.urls`
#: ends in a bundle-name catch-all whose regex matches every name below, so an
#: unserved one resolves to "is there a bundle called that?" and answers with a
#: user-visible error.
#:
#: Keep this list in step with `deploy/roles/nginx/templates/favicon.conf`. A
#: name in neither place goes back to being a bundle-name lookup that scolds
#: the reader.
ROOT_ASSETS = (
    "favicon.ico",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "apple-touch-icon.png",
    "safari-pinned-tab.svg",
    "site.webmanifest",
    "browserconfig.xml",
    "mstile-150x150.png",
    "android-chrome-192x192.png",
    "android-chrome-256x256.png",
)


def root_asset(request, asset):
    """Redirect a root-level asset request to where the file actually is.

    A redirect rather than serving the bytes: Django is not the right thing to
    stream static files through, and in production this view is unreachable
    anyway because nginx aliases the same names first.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param asset: file name, one of :data:`ROOT_ASSETS`
    :type asset: str
    :return: :class:`django.http.HttpResponseRedirect`
    """
    return redirect(static(asset))


urlpatterns = [
    # sitemap
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    re_path(
        r"^sitemap/$",
        sitemap,
        {
            "sitemaps": sitemaps,
            "template_name": "sitemap.html",
            "content_type": None,
        },
        name="sitemap",
    ),
    # walletauth app namespace
    re_path(r"^api/v2/wallet/", include(walletauth_urls)),
    # api app namespace
    re_path(r"^api/v2/", include(api_urls)),
    # allauth
    re_path(r"^accounts/", include("allauth.urls")),
    # captcha namespace
    re_path(r"^captcha/", include("captcha.urls")),
    # widgets app namespace
    re_path(r"^widgets/", include(widget_urls)),
    # Root-level browser assets, ahead of the catch-all that would other-
    # wise read them as bundle names. See ROOT_ASSETS above.
    re_path(
        r"^(?P<asset>{})$".format("|".join(re.escape(name) for name in ROOT_ASSETS)),
        root_asset,
    ),
    # core app namespace
    re_path(r"^", include(core_urls)),
]

handler500 = "core.views.custom_server_error"

# if settings.DEBUG:  # pragma: no cover
#     from debug_toolbar.toolbar import debug_toolbar_urls

#     urlpatterns += debug_toolbar_urls()

#     # from django.conf.urls.static import static

#     # urlpatterns += static("/", document_root=settings.STATIC_ROOT)
#     # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
