"""Testing module for :py:mod:`core.views_app` module."""

import json

import pytest
from django.test import override_settings
from django.urls import reverse

from core.views_app import AASA_EXCLUDED_PATHS, APP_ID


@pytest.mark.django_db
class TestCoreViewsAppAppleAppSiteAssociation:
    """Testing class for :py:func:`core.views_app.apple_app_site_association`."""

    def _get(self, client):
        response = client.get("/.well-known/apple-app-site-association")
        return response, json.loads(response.content)

    def test_core_views_app_aasa_url_has_no_suffix(self):
        assert reverse("apple_app_site_association") == (
            "/.well-known/apple-app-site-association"
        )

    def test_core_views_app_aasa_is_json_without_redirect(self, client):
        response, _ = self._get(client)

        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"

    def test_core_views_app_aasa_names_the_app(self, client):
        _, document = self._get(client)

        assert document["applinks"]["details"][0]["appIDs"] == [f"DF2V3954Z7.{APP_ID}"]

    @override_settings(APPLE_APP_ID_PREFIX="ABCDE12345")
    def test_core_views_app_aasa_team_from_settings(self, client):
        _, document = self._get(client)

        assert document["applinks"]["details"][0]["appIDs"] == [f"ABCDE12345.{APP_ID}"]

    def test_core_views_app_aasa_excludes_before_including_everything(self, client):
        _, document = self._get(client)
        components = document["applinks"]["details"][0]["components"]

        assert components[:-1] == [
            {"/": path, "exclude": True} for path in AASA_EXCLUDED_PATHS
        ]
        assert components[-1] == {"/": "/*"}

    @pytest.mark.parametrize(
        "path", ["/accounts/*", "/api/*", "/app/auth/*", "/static/*", "/admin/*", "/captcha/*"]
    )
    def test_core_views_app_aasa_excluded_paths(self, path):
        assert path in AASA_EXCLUDED_PATHS


@pytest.mark.django_db
class TestCoreViewsAppAssetlinks:
    """Testing class for :py:func:`core.views_app.assetlinks`."""

    def _get(self, client):
        response = client.get("/.well-known/assetlinks.json")
        return response, json.loads(response.content)

    def test_core_views_app_assetlinks_url(self):
        assert reverse("assetlinks") == "/.well-known/assetlinks.json"

    @override_settings(ANDROID_CERT_SHA256=())
    def test_core_views_app_assetlinks_empty_without_fingerprints(self, client):
        response, document = self._get(client)

        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        assert document == []

    @override_settings(ANDROID_CERT_SHA256=("AA:BB", "CC:DD"))
    def test_core_views_app_assetlinks_with_fingerprints(self, client):
        _, document = self._get(client)

        assert document == [
            {
                "relation": ["delegate_permission/common.handle_all_urls"],
                "target": {
                    "namespace": "android_app",
                    "package_name": APP_ID,
                    "sha256_cert_fingerprints": ["AA:BB", "CC:DD"],
                },
            }
        ]
