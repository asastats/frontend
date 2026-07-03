"""Module containing api app's URL configurations."""

from django.urls import include, path, re_path
from django_minify_html.decorators import no_html_minification
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from api import views as api_views


def _nested_account_patterns(type):
    """Return collection of URL resolvers for provided account type.

    :param type: account type (address, bundle, or NFD name)
    :type type: str
    :return: list
    """
    return [
        path(
            r"",
            getattr(api_views, f"{type}View").as_view(),
            name=f"api_v2_{type.lower()}",
        ),
        path(
            r"asas/",
            getattr(api_views, f"{type}ViewAsas").as_view(),
            kwargs={"id": True},
            name=f"api_v2_{type.lower()}_asas",
        ),
        path(
            r"asas/<int:id>/",
            getattr(api_views, f"{type}ViewAsasAsset").as_view(),
            name=f"api_v2_{type.lower()}_asas_asset",
        ),
        path(
            r"nfts/",
            getattr(api_views, f"{type}ViewNfts").as_view(),
            kwargs={"id": True},
            name=f"api_v2_{type.lower()}_nfts",
        ),
        path(
            r"nfts/<int:id>/",
            getattr(api_views, f"{type}ViewNftsAsset").as_view(),
            name=f"api_v2_{type.lower()}_nfts_asset",
        ),
        path(
            r"nftcollections/",
            getattr(api_views, f"{type}ViewNftCollections").as_view(),
            kwargs={"name": True},
            name=f"api_v2_{type.lower()}_nftcollections",
        ),
        path(
            r"nftcollections/<str:name>/",
            getattr(api_views, f"{type}ViewNftCollectionsCollection").as_view(),
            name=f"api_v2_{type.lower()}_nftcollections_collection",
        ),
        path(
            r"entities/",
            getattr(api_views, f"{type}Entities").as_view(),
            name=f"api_v2_{type.lower()}_entities",
        ),
    ]


schema_view = SpectacularAPIView.as_view()
swagger_view = SpectacularSwaggerView.as_view(url_name="api_schema")
redoc_view = SpectacularRedocView.as_view(url_name="api_schema")
schema_view = no_html_minification(schema_view)
swagger_view = no_html_minification(swagger_view)
redoc_view = no_html_minification(redoc_view)

urlpatterns = [
    ## API
    re_path(r"$", api_views.RawPostView.as_view(), name="api_v2_raw"),
    re_path(
        r"(?P<address>[0-9A-Za-z]{58})/",
        include(_nested_account_patterns("Address")),
    ),
    re_path(
        r"(?P<bundle>[0-9A-Za-z]{40})/",
        include(_nested_account_patterns("Bundle")),
    ),
    re_path(
        r"(?P<nfd_name>[-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/",
        include(_nested_account_patterns("NfdName")),
    ),
    ## API token
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    ## OpenAPI schema
    path("schema/", schema_view, name="api_schema"),
    path("schema/swagger-ui/", swagger_view, name="swagger-ui"),
    path("schema/redoc/", redoc_view, name="redoc"),
    path("settings/", api_views.SettingsView.as_view(), name="api_v2_settings"),
    re_path(
        r"(?P<name>[-\w]*\.*[-\w]+)/$",
        api_views.BundleNameView.as_view(),
        name="api_v2_name",
    ),
]
