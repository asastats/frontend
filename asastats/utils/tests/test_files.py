"""Testing module for checking the existence of required files."""

import os

import pytest
from django.conf import settings


class TestFiles:
    """Testing class used to check the existence of required files."""

    def test_files_favicon_exists(self):
        path = os.path.abspath(os.path.join(settings.STATIC_ROOT, "favicon.ico"))
        assert os.path.exists(path)

    def test_files_logo_image_exist(self):
        path = os.path.abspath(os.path.join(settings.STATIC_ROOT, "img/logo.png"))
        assert os.path.exists(path)

    @pytest.mark.parametrize("version", ["asastats.png", "asastats-dark.png"])
    def test_files_brand_images_exist(self, version):
        path = os.path.abspath(
            os.path.join(settings.STATIC_ROOT, "img/{}".format(version))
        )
        assert os.path.exists(path)

    @pytest.mark.parametrize(
        "asset", ["logo", "logo400", "icon", "colors", "logo-dark"]
    )
    def test_files_assets_png_images_exist(self, asset):
        path = os.path.abspath(
            os.path.join(settings.STATIC_ROOT, "assets/asastats-{}.png".format(asset))
        )
        assert os.path.exists(path)

    def test_files_assets_svg_image_exist(self):
        path = os.path.abspath(
            os.path.join(settings.STATIC_ROOT, "assets/asastats-logo.svg")
        )
        assert os.path.exists(path)

    @pytest.mark.parametrize(
        "image",
        ["discord.png", "github.png", "google.png", "reddit.png", "twitter.png"],
    )
    def test_files_login_by_social_images_exist(self, image):
        path = os.path.abspath(
            os.path.join(settings.STATIC_ROOT, "img/social/{}".format(image))
        )
        assert os.path.exists(path)

    @pytest.mark.parametrize(
        "image", ["discord24.png", "github24.png", "reddit24.png", "twitter24.png"]
    )
    def test_files_social_images_for_email_exist(self, image):
        path = os.path.abspath(
            os.path.join(settings.STATIC_ROOT, "img/social/{}".format(image))
        )
        assert os.path.exists(path)
