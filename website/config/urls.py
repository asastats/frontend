"""Website URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path

from api import urls as api_urls
from core import urls as core_urls
from walletauth import urls as walletauth_urls
from widgets import urls as widget_urls

from .sitemaps import PrioritizedStaticViewSitemap, StaticViewSitemap

sitemaps = {"statichp": PrioritizedStaticViewSitemap, "static": StaticViewSitemap}


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
