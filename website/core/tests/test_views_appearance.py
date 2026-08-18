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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS


class ProfileAppearanceViewTest(TestCase):
    """Testing class for the appearance page."""

    def setUp(self):
        self.url = reverse("profile_appearance")

    def _sign_in(
        self,
        username="appearance@example.com",
        permission=SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
    ):
        """Signed in AND entitled by default.

        Reaching this page is itself a subscription feature now -- the view
        redirects anyone below Asastatser -- so a bare signed-in user is no
        longer a reader of this page.
        """
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
        """May use the typefaces: Professional and up."""
        return self._sign_in(
            "paid@example.com", SUBSCRIPTION_TIER_PERMISSIONS["Professional"]
        )

    def _unentitled(self):
        """May open the page, but not the Fonts tab.

        Asastatser exactly: the tier that reaches the page and every theme on
        it, and stops one short of the typefaces.
        """
        return self._sign_in(
            "themes@example.com", SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
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
        # Above the tier Fonts is a tab like Dark and Light: a radio input,
        # with the pairings in the panel behind it.
        self.assertContains(response, 'name="typeface-choice"')

    def test_core_views_appearance_unentitled_reader_may_not(self):
        self._unentitled()

        response = self.client.get(self.url)

        self.assertFalse(response.context["can_access_typeface"])

    def test_core_views_appearance_unentitled_reader_gets_no_dead_controls(self):
        """Below the tier the Fonts tab is a link, not a panel of dead radios.

        It used to render every pairing disabled, which read as a control that
        had stopped working rather than one that has a price. Asserting the
        exact string the entitled test asserts is present, so the two cannot
        both pass by accident.
        """
        self._unentitled()

        response = self.client.get(self.url)

        self.assertNotContains(response, 'name="typeface-choice"')

    def test_core_views_appearance_unentitled_fonts_tab_is_the_upgrade_path(self):
        """Clicking Fonts has to go somewhere the reader can act."""
        self._unentitled()

        response = self.client.get(self.url)
        html = response.content.decode()

        tab = html[html.index('id="id-tab-fonts"') - 200:]
        tab = tab[: tab.index(">", tab.index('id="id-tab-fonts"')) + 1]
        self.assertIn(reverse("subscriptions"), tab)

    def test_core_views_appearance_unentitled_reader_is_pointed_at_subscriptions(self):
        self._unentitled()

        response = self.client.get(self.url)

        self.assertContains(response, reverse("subscriptions"))
        # The tier named is the one that unlocks typefaces, which is no longer
        # the tier that unlocks this page.
        self.assertContains(response, "Professional")

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


class ProfileAppearanceTabsTest(TestCase):
    """The page is three tabs: Dark, Light, Fonts.

    57 swatches in one column meant scrolling past every dark theme to reach a
    light one, and the typeface section sat below all of them where a reader
    had to already know it was there.
    """

    def setUp(self):
        self.url = reverse("profile_appearance")

    def _sign_in(self, permission=SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]):
        """Entitled by default: the view redirects anyone below Asastatser."""
        user = get_user_model().objects.create_user(
            username="tabs@example.com", email="tabs@example.com", password="x"
        )
        profile = user.profile
        profile.permission = permission
        profile.save()
        self.client.force_login(user)
        return user

    def test_core_views_appearance_has_a_tab_per_scheme(self):
        self._sign_in()

        response = self.client.get(self.url)

        self.assertContains(response, 'id="id-tab-dark"')
        self.assertContains(response, 'id="id-tab-light"')
        self.assertContains(response, 'id="id-tab-fonts"')

    def test_core_views_appearance_tabs_do_not_collide_with_the_pickers(self):
        """Three radio groups share this page and must stay separate.

        A tab named `theme-dropdown` would make switching tabs change the
        theme, and clear whichever theme was chosen.
        """
        self._sign_in()

        response = self.client.get(self.url)
        html = response.content.decode()

        tabs = html.count('name="appearance-tab"')
        self.assertGreaterEqual(tabs, 2)
        self.assertNotIn('name="appearance-tab" value=', html)

    def _tab_region(self, response):
        """Just the tabs.

        The header carries its own picker listing every theme, and it renders
        before this section -- searching the whole page finds those first and
        would have every assertion here passing on the wrong control.
        """
        html = response.content.decode()
        return html[html.index('id="id-appearance-tabs"'):]

    def test_core_views_appearance_light_tab_holds_the_light_themes(self):
        """Light comes first, matching the order the header dropdown uses."""
        self._sign_in()

        response = self.client.get(self.url)
        html = self._tab_region(response)
        light_at = html.index('id="id-tab-light"')
        dark_at = html.index('id="id-tab-dark"')

        self.assertLess(light_at, dark_at, "Dark is offered before Light")
        for theme in settings.AVAILABLE_THEMES_BY_SCHEME["Light"]:
            at = html.index(f'value="{theme}"')
            self.assertTrue(
                light_at < at < dark_at, f"{theme} is not under the Light tab"
            )

    def test_core_views_appearance_dark_tab_holds_the_dark_themes(self):
        self._sign_in()

        response = self.client.get(self.url)
        html = self._tab_region(response)
        dark_at = html.index('id="id-tab-dark"')

        for theme in settings.AVAILABLE_THEMES_BY_SCHEME["Dark"]:
            self.assertGreater(
                html.index(f'value="{theme}"'),
                dark_at,
                f"{theme} is not under the Dark tab",
            )

    def test_core_views_appearance_every_theme_appears_exactly_once(self):
        """Two tabs over one list: a theme in both would be two controls."""
        self._sign_in()

        response = self.client.get(self.url)
        html = self._tab_region(response)

        for theme in settings.AVAILABLE_THEMES:
            self.assertEqual(
                html.count(f'name="theme-dropdown" value="{theme}"'),
                1,
                f"{theme} is offered more than once",
            )

    def test_core_views_appearance_opens_on_a_tab_without_scripting(self):
        """The tabs are radios, so one must be checked in the markup itself.

        theme.js moves the selection to whichever tab holds the active theme,
        but a reader whose JavaScript failed still needs a populated panel
        rather than three headings over nothing.
        """
        self._sign_in()

        response = self.client.get(self.url)

        # Light is the one marked checked in the markup, so that is the panel
        # a reader without scripting lands on -- and it is the first tab, so
        # the page does not open on a tab that is not the leftmost.
        html = response.content.decode()
        light_at = html.index('id="id-tab-light"')
        checked_at = html.index("checked", light_at)
        dark_at = html.index('id="id-tab-dark"')

        self.assertLess(checked_at, dark_at, "the Light tab is not the checked one")
