"""Testing module for :py:mod:`core.views` decorators."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

user_model = get_user_model()


class LoginRequiredDecoratorUsedTest(TestCase):
    def test_anonymous_can_get_robots_file(self):
        response = self.client.get(reverse("index_file", args=["robots.txt"]))

        self.assertEqual(response.status_code, 200)

    def test_anonymous_can_get_google_ownership_file(self):
        response = self.client.get(
            reverse("index_file", args=[settings.GOOGLE_OWNERSHIP_FILE])
        )

        self.assertEqual(response.status_code, 200)

    def test_anonymous_can_get_png_assets_file(self):
        response = self.client.get(reverse("assets_file", args=["logo.png"]))

        self.assertEqual(response.status_code, 200)

    def test_anonymous_can_get_svg_assets_file(self):
        response = self.client.get(reverse("assets_file", args=["logo.svg"]))

        self.assertEqual(response.status_code, 200)

    def test_anonymous_can_get_logo400_png_assets_file(self):
        response = self.client.get(reverse("assets_file", args=["logo400.png"]))

        self.assertEqual(response.status_code, 200)

    def test_anonymous_can_get_social24_png_assets_file(self):
        response = self.client.get(reverse("social_icons", args=["discord24.png"]))

        self.assertEqual(response.status_code, 200)

    def test_anonymous_can_get_index_page(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_can_get_login_page(self):
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_can_get_signup_page(self):
        response = self.client.get(reverse("account_signup"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_redirects_to_login_page_for_home_page(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, "/accounts/login/?next=/home/")

    def test_anonymous_redirects_to_login_page_for_profile_page(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(response, "/accounts/login/?next=/profile/")
