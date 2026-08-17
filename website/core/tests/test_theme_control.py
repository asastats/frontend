"""The appearance control is two controls, and which one renders matters.

A signed-out reader gets a light/dark switch between the two brand themes. A
signed-in reader gets the full list, with Customize leading to the appearance
page. Getting this backwards fails silently in the worst way: a signed-out
reader offered 38 themes can pick one, see it apply, and find it has followed
them nowhere -- or a signed-in reader loses the entry point to the page
entirely and the appearance feature becomes unreachable.

Rendered through a real page rather than the snippet alone, because the
snippet depends on context processors and on `user`, and testing it in
isolation would assert less than it appears to.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ThemeControlTest(TestCase):
    """Testing class for the header appearance control."""

    def setUp(self):
        # A page every reader can reach, signed in or not.
        self.url = reverse("about")

    def _sign_in(self, username="themes@example.com"):
        user = get_user_model().objects.create_user(
            username=username, email=username, password="top_secret"
        )
        self.client.force_login(user)
        return user

    # # signed out
    def test_core_theme_control_anonymous_gets_a_light_dark_switch(self):
        response = self.client.get(self.url)

        self.assertContains(response, "data-theme-toggle")

    def test_core_theme_control_anonymous_switch_carries_both_brand_themes(self):
        """The pair comes from settings, so the script never names a theme."""
        response = self.client.get(self.url)

        self.assertContains(response, f'data-theme-light="{settings.BRAND_THEME_LIGHT}"')
        self.assertContains(response, f'data-theme-dark="{settings.BRAND_THEME_DARK}"')

    def test_core_theme_control_anonymous_gets_no_theme_list(self):
        """The full list is a signed-in feature."""
        response = self.client.get(self.url)

        self.assertNotContains(response, 'name="theme-dropdown"')

    def test_core_theme_control_anonymous_gets_no_customize_link(self):
        """Customize leads to a signed-in page; offering it would be a dead end."""
        response = self.client.get(self.url)

        self.assertNotContains(response, reverse("profile_appearance"))

    # # signed in
    def test_core_theme_control_signed_in_gets_the_theme_list(self):
        self._sign_in()

        response = self.client.get(self.url)

        self.assertContains(response, 'name="theme-dropdown"')

    def test_core_theme_control_signed_in_gets_a_customize_link(self):
        """The dropdown's first entry is the way to the appearance page."""
        self._sign_in()

        response = self.client.get(self.url)

        self.assertContains(response, reverse("profile_appearance"))

    def test_core_theme_control_signed_in_gets_no_bare_switch(self):
        """The two controls are alternatives, never both.

        Rendering both would put two appearance affordances in the header,
        and the switch would silently overwrite a chosen theme.
        """
        self._sign_in()

        response = self.client.get(self.url)

        self.assertNotContains(response, "data-theme-toggle")

    def test_core_theme_control_signed_in_list_is_grouped(self):
        """38 names in one list is what the grouping exists to prevent."""
        self._sign_in()

        response = self.client.get(self.url)

        for group in response.context["AVAILABLE_THEMES_BY_SCHEME"]:
            self.assertContains(response, group)
