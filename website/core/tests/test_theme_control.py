"""The appearance control is three controls, and which one renders matters.

Signing in is not what separates them -- a subscription is:

* below Intro, signed in or not: a light/dark switch between the two brand
  themes, and nothing else;
* Intro: the twelve themes in `settings.DEFAULT_THEMES`, with no Customize
  link and no credit line, because that tier reaches neither the appearance
  page nor any theme requiring attribution;
* Asastatser and up: the same twelve plus Customize, which leads to the page
  where every theme lives and the credit is rendered.

Getting this wrong fails quietly in both directions: a reader offered themes
their tier cannot keep, or a paying reader who loses the entry point to the
page they paid for.

Rendered through a real page rather than the snippet alone, because the
snippet depends on context processors and on `user`, and testing it in
isolation would assert less than it appears to.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS


class ThemeControlTest(TestCase):
    """Testing class for the header appearance control."""

    def setUp(self):
        # A page every reader can reach, signed in or not.
        self.url = reverse("about")

    def _sign_in(self, username="themes@example.com", tier=None):
        """Sign in at a tier. `None` means signed in with no subscription."""
        user = get_user_model().objects.create_user(
            username=username, email=username, password="top_secret"
        )
        if tier:
            user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS[tier]
            user.profile.save()
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
        """Choosing a theme is a subscription feature, not a sign-in one."""
        response = self.client.get(self.url)

        self.assertNotContains(response, 'name="theme-dropdown"')

    def test_core_theme_control_anonymous_gets_no_customize_link(self):
        """Customize leads to a signed-in page; offering it would be a dead end."""
        response = self.client.get(self.url)

        self.assertNotContains(response, reverse("profile_appearance"))

    # # signed in
    def test_core_theme_control_signed_in_without_a_tier_gets_the_switch(self):
        """Signing in buys nothing here: same control a visitor gets."""
        self._sign_in()

        response = self.client.get(self.url)

        self.assertContains(response, "data-theme-toggle")
        self.assertNotContains(response, 'name="theme-dropdown"')

    def test_core_theme_control_intro_gets_the_theme_list(self):
        self._sign_in(tier="Intro")

        response = self.client.get(self.url)

        self.assertContains(response, 'name="theme-dropdown"')

    def test_core_theme_control_intro_gets_no_customize_link(self):
        """Intro cannot open that page, so the link would be a dead end."""
        self._sign_in(tier="Intro")

        response = self.client.get(self.url)

        self.assertNotContains(response, reverse("profile_appearance"))

    def test_core_theme_control_intro_sees_no_attribution_credit(self):
        """And so must be offered no theme that requires one.

        The credit CC BY asks for is rendered on the appearance page and in
        this dropdown's footer, and Intro reaches neither -- which is why
        `DEFAULT_THEMES` may not draw on `THEME_ATTRIBUTION`.
        """
        self._sign_in(tier="Intro")

        response = self.client.get(self.url)

        self.assertNotContains(response, settings.THEME_ATTRIBUTION["license"])

    def test_core_theme_control_asastatser_gets_a_customize_link(self):
        """The dropdown's first entry is the way to the appearance page."""
        self._sign_in(tier="Asastatser")

        response = self.client.get(self.url)

        self.assertContains(response, reverse("profile_appearance"))

    def test_core_theme_control_asastatser_sees_the_attribution_credit(self):
        """It names themes that tier can reach, so the credit is due."""
        self._sign_in(tier="Asastatser")

        response = self.client.get(self.url)

        self.assertContains(response, settings.THEME_ATTRIBUTION["license"])

    def test_core_theme_control_subscriber_gets_no_bare_switch(self):
        """The two controls are alternatives, never both.

        Rendering both would put two appearance affordances in the header,
        and the switch would silently overwrite a chosen theme.
        """
        self._sign_in(tier="Intro")

        response = self.client.get(self.url)

        self.assertNotContains(response, "data-theme-toggle")

    def test_core_theme_control_list_is_grouped(self):
        """Twelve names in one list is what the grouping exists to prevent."""
        self._sign_in(tier="Intro")

        response = self.client.get(self.url)

        for group in response.context["DEFAULT_THEMES_BY_SCHEME"]:
            self.assertContains(response, group)

    # # exactly one control per page
    #
    # index is the only page that blanks the header block, so it carries its
    # own control. The first attempt put one in the footer instead, which gave
    # every *other* page two of them: a duplicated `id-theme-list`, and two
    # radio groups sharing the name `theme-dropdown`, so the two menus fought
    # over which theme was ticked. Nothing in the suite failed on the duplicate
    # id -- it surfaced as a count mismatch in an unrelated assertion.
    def test_core_theme_control_renders_once_for_a_subscriber(self):
        self._sign_in(tier="Intro")

        response = self.client.get(self.url)

        self.assertContains(response, 'id="id-theme-list"', count=1)

    def test_core_theme_control_renders_once_for_an_anonymous_reader(self):
        response = self.client.get(self.url)

        self.assertContains(response, "data-theme-toggle", count=1)

    def test_core_theme_control_renders_once_on_index_signed_in(self):
        """index supplies its own, and must not also inherit one."""
        self._sign_in(tier="Intro")

        response = self.client.get(reverse("index"))

        self.assertContains(response, 'id="id-theme-list"', count=1)

    def test_core_theme_control_renders_once_on_index_anonymous(self):
        response = self.client.get(reverse("index"))

        self.assertContains(response, "data-theme-toggle", count=1)
