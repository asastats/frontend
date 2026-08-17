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

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS


class ProfileAppearanceViewTest(TestCase):
    """Testing class for the appearance page."""

    def setUp(self):
        self.url = reverse("profile_appearance")

    def _sign_in(self, username="appearance@example.com", permission=0):
        user = get_user_model().objects.create_user(
            username=username, email=username, password="top_secret"
        )
        if permission:
            user.profile.permission = permission
            user.profile.save()
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


class ProfileAppearanceTypefaceTest(TestCase):
    """Testing class for the typeface section and its subscription gate.

    Choosing a *theme* is free to any signed-in reader; borrowing another
    theme's typeface pairing is not. The gate follows the explorer preference
    on the settings page: below the tier the choices are still rendered, but
    disabled and wrapped in a link to subscriptions, so the reader can see what
    the upgrade buys.
    """

    def setUp(self):
        self.url = reverse("profile_appearance")

    def _sign_in(self, username, permission=0):
        user = get_user_model().objects.create_user(
            username=username, email=username, password="top_secret"
        )
        user.profile.permission = permission
        user.profile.save()
        self.client.force_login(user)
        return user

    def _entitled(self):
        return self._sign_in(
            "paid@example.com", SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        )

    def _unentitled(self):
        return self._sign_in(
            "free@example.com", SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"] - 1
        )

    # # the catalogue
    def test_core_views_appearance_publishes_the_typeface_catalogue(self):
        """The pairings come from the generated file, not from the template.

        build-typefaces.py writes typefaces.json and typefaces.css in one run,
        so a pairing offered here is one the stylesheet can actually apply.
        """
        self._entitled()

        response = self.client.get(self.url)
        typefaces = response.context["typefaces"]

        assert typefaces, "no typeface pairings were published"
        for name, faces in typefaces.items():
            assert faces.get("display"), f"{name} has no display face"
            assert faces.get("sans"), f"{name} has no body face"

    def test_core_views_appearance_offers_every_pairing(self):
        self._entitled()

        response = self.client.get(self.url)
        html = response.content.decode()

        missing = [
            name
            for name in response.context["typefaces"]
            if f'value="{name}"' not in html
        ]
        self.assertEqual(missing, [], f"pairings not rendered: {missing}")

    def test_core_views_appearance_offers_a_way_back_to_the_theme_default(self):
        """An empty value clears the override rather than setting a pairing."""
        self._entitled()

        response = self.client.get(self.url)

        self.assertContains(response, 'name="typeface-choice" value=""')

    def test_core_views_appearance_previews_each_pairing_in_itself(self):
        """`data-typeface` is what makes the specimen render in its own face."""
        self._entitled()

        response = self.client.get(self.url)
        html = response.content.decode()

        unpreviewed = [
            name
            for name in response.context["typefaces"]
            if f'data-typeface="{name}"' not in html
        ]
        self.assertEqual(unpreviewed, [], f"pairings without a specimen: {unpreviewed}")

    # # the gate
    def test_core_views_appearance_entitled_reader_may_choose(self):
        self._entitled()

        response = self.client.get(self.url)

        self.assertTrue(response.context["can_access_typeface"])
        # The same string the unentitled test asserts is present, so the two
        # cannot both pass by accident.
        self.assertNotContains(response, 'disabled aria-disabled="true"')

    def test_core_views_appearance_unentitled_reader_may_not(self):
        self._unentitled()

        response = self.client.get(self.url)

        self.assertFalse(response.context["can_access_typeface"])

    def test_core_views_appearance_unentitled_reader_still_sees_the_choices(self):
        """Hiding them would make the upgrade an abstraction.

        The explorer preference does the same: render the control, disable it,
        and let a click lead to subscriptions.
        """
        self._unentitled()

        response = self.client.get(self.url)
        html = response.content.decode()

        for name in response.context["typefaces"]:
            self.assertIn(f'value="{name}"', html)

    def test_core_views_appearance_unentitled_choices_are_disabled(self):
        """Rendered is not the same as usable."""
        self._unentitled()

        response = self.client.get(self.url)

        self.assertContains(response, "disabled aria-disabled=\"true\"")

    def test_core_views_appearance_unentitled_reader_is_pointed_at_subscriptions(self):
        self._unentitled()

        response = self.client.get(self.url)

        self.assertContains(response, reverse("subscriptions"))
        self.assertContains(response, "Asastatser")

    def test_core_views_appearance_theme_choice_is_not_gated(self):
        """The tier buys typefaces, not themes.

        A reader below the tier must still get the full theme list -- gating
        both would be an easy mistake to make in one template edit.
        """
        self._unentitled()

        response = self.client.get(self.url)
        html = response.content.decode()

        for theme in response.context["AVAILABLE_THEMES"]:
            self.assertIn(f'value="{theme}"', html)
