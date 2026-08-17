"""Testing module for :py:class:`core.views.ProfileAppearanceView`.

The page carries no state of its own -- the theme is stored in the browser and
never sent to the server -- so what is worth asserting is the plumbing around
it: that it is signed-in only, that it renders the list the picker renders, and
that the two controls cannot drift apart.

That last point is the reason this file exists. The header dropdown and this
page are two entry points to the same choice, wired to the same radio name by
static/js/theme.js. A page offering a theme the header does not (or the other
way round) would not fail anywhere: it would just quietly be two features.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ProfileAppearanceViewTest(TestCase):
    """Testing class for the appearance page."""

    def setUp(self):
        self.url = reverse("profile_appearance")

    def _sign_in(self, username="appearance@example.com"):
        user = get_user_model().objects.create_user(
            username=username, email=username, password="top_secret"
        )
        self.client.force_login(user)
        return user

    def test_core_views_appearance_requires_a_signed_in_reader(self):
        """Choosing a theme is a signed-in feature; the switch is not.

        A signed-out reader gets the light/dark toggle in the header. Reaching
        this page anonymously must send them to log in rather than render a
        chooser they were not offered.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_core_views_appearance_renders_for_a_signed_in_reader(self):
        self._sign_in()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_appearance.html")
        self.assertTemplateUsed(response, "base_profile.html")

    def test_core_views_appearance_offers_every_theme(self):
        """One selectable control per offered theme, and no others."""
        self._sign_in()

        response = self.client.get(self.url)
        html = response.content.decode()

        missing = [
            theme
            for theme in response.context["AVAILABLE_THEMES"]
            if f'value="{theme}"' not in html
        ]
        self.assertEqual(
            missing,
            [],
            f"themes offered in settings but not rendered on the page: {missing}",
        )

    def test_core_views_appearance_previews_each_theme_in_itself(self):
        """Each swatch must carry `data-theme`, or the preview is a lie.

        The point of the page is choosing by eye. Without the attribute every
        swatch renders in the *current* theme and they all look identical,
        which is exactly the flat list of names the page exists to replace.
        """
        self._sign_in()

        response = self.client.get(self.url)
        html = response.content.decode()

        unpreviewed = [
            theme
            for theme in response.context["AVAILABLE_THEMES"]
            if f'data-theme="{theme}"' not in html
        ]
        self.assertEqual(
            unpreviewed,
            [],
            f"themes rendered without their own preview: {unpreviewed}",
        )

    def test_core_views_appearance_uses_the_same_control_as_the_header(self):
        """`theme-dropdown` is what static/js/theme.js binds.

        Renaming it here would leave the page looking right and doing nothing,
        with no error to notice.
        """
        self._sign_in()

        response = self.client.get(self.url)

        self.assertContains(response, 'name="theme-dropdown"')

    def test_core_views_appearance_credits_the_third_party_themes(self):
        """CC BY attribution has to appear wherever the themes are offered."""
        self._sign_in()

        response = self.client.get(self.url)
        attribution = response.context["THEME_ATTRIBUTION"]

        self.assertContains(response, attribution["author"])
        self.assertContains(response, attribution["license"])
