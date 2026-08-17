"""Functional tests for the appearance controls.

The site used to offer one alternative appearance -- a dark/light toggle whose
every rule was hand-written, because Materialize has no dark mode. Themes come
from ``settings.AVAILABLE_THEMES`` now, and the choice is stored client-side
and never sent to the server, so most of what matters here is that the choice
survives a page change.

There are two controls, and which one a reader gets depends on who they are:

* signed out -- a light/dark switch between the two brand themes, and nothing
  else. The full list is a signed-in feature, so offering it to someone who
  cannot reach the appearance page would be a menu that mostly does not apply;
* signed in -- the full list in the header, plus the appearance page behind
  Customize, where the choice is made by looking rather than by reading names.

Both are driven by the same `theme.js`, and the tests below are grouped by
which control they exercise.
"""

from django.conf import settings
from django.urls import reverse

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from selenium.webdriver.common.by import By

from .base import FunctionalTest


class AppearancePickerTest(FunctionalTest):
    """The signed-in picker: what it offers, and what choosing does."""

    def _open_picker(self, page="disclaimer"):
        # The list is rendered only for a signed-in reader, so every test in
        # this class needs a session before it can see one.
        self.create_cookie_and_go_to_index_page("picker@example.com")
        self.browser.get(self.server_url + reverse(page))
        # A <details>, so it opens without scripting; open it directly rather
        # than clicking, which keeps the test about the choice, not the widget.
        self.browser.execute_script(
            "document.querySelector('#id-theme-list').closest('details').open = true;"
        )
        return self.browser.find_elements(
            By.CSS_SELECTOR, "#id-theme-list input[name='theme-dropdown']"
        )

    def _stamped_theme(self):
        return self.browser.find_element(By.TAG_NAME, "html").get_attribute(
            "data-theme"
        )

    def test_picker_offers_exactly_the_themes_settings_declares(self):
        """The picker is rendered from settings, so adding a theme is a
        settings change plus an input.css registration -- never a template
        edit. core.tests.test_context_processors keeps those two in step."""
        radios = self._open_picker()
        self.assertEqual(
            [r.get_attribute("value") for r in radios],
            list(settings.AVAILABLE_THEMES),
        )

    def test_no_theme_is_stamped_until_one_is_chosen(self):
        self.create_cookie_and_go_to_index_page("unstamped@example.com")
        self.browser.get(self.server_url + reverse("disclaimer"))
        # Unstamped means DaisyUI's own default applies -- the `asastats` theme
        # is registered with `default: true`, so the page is still branded.
        self.assertIsNone(self._stamped_theme())

    def test_choosing_a_theme_applies_it_and_survives_a_page_change(self):
        radios = self._open_picker()
        target = next(r for r in radios if r.get_attribute("value") == "abyss")
        self.browser.execute_script(
            "arguments[0].checked = true;"
            "arguments[0].dispatchEvent(new Event('change'));",
            target,
        )
        self.wait_until(lambda: self._stamped_theme() == "abyss")

        # The choice is client-side only, so it has to come back from storage,
        # and early enough that the page never paints the default first.
        self.browser.get(self.server_url + reverse("faq"))
        self.wait_until(lambda: self._stamped_theme() == "abyss")

    def test_the_picker_closes_once_a_theme_is_chosen(self):
        radios = self._open_picker()
        menu = self.browser.find_element(
            By.CSS_SELECTOR, "#id-theme-list"
        ).find_element(By.XPATH, "./ancestor::details")
        self.browser.execute_script(
            "arguments[0].dispatchEvent(new Event('change'));", radios[0]
        )
        self.wait_until(lambda: menu.get_attribute("open") is None)

    def test_the_picker_is_reachable_from_every_page_that_has_the_new_header(self):
        # index deliberately blanks {% block header %} -- it is a bare
        # landing page -- so it has no picker to find.
        self.create_cookie_and_go_to_index_page("everypage@example.com")
        for page in ("faq", "subscriptions", "account_login", "disclaimer"):
            with self.subTest(page=page):
                self.browser.get(self.server_url + reverse(page))
                self.assertTrue(self.browser.find_elements(By.ID, "id-theme-list"))


class AnonymousThemeSwitchTest(FunctionalTest):
    """The signed-out control: a light/dark switch, and only that."""

    def _switch(self, page="disclaimer"):
        self.browser.get(self.server_url + reverse(page))
        return self.browser.find_element(By.CSS_SELECTOR, "[data-theme-toggle]")

    def _stamped_theme(self):
        return self.browser.find_element(By.TAG_NAME, "html").get_attribute(
            "data-theme"
        )

    def test_a_signed_out_reader_gets_a_switch_and_no_theme_list(self):
        """The full list is a signed-in feature.

        Offering 38 themes to someone who cannot reach the appearance page
        would be a menu that mostly does not apply to them.
        """
        self._switch()

        self.assertFalse(self.browser.find_elements(By.ID, "id-theme-list"))

    def test_the_switch_turns_the_page_dark_then_light_again(self):
        switch = self._switch()

        switch.click()
        self.wait_until(lambda: self._stamped_theme() == settings.BRAND_THEME_DARK)

        switch.click()
        self.wait_until(lambda: self._stamped_theme() == settings.BRAND_THEME_LIGHT)

    def test_the_choice_survives_a_page_change(self):
        """Stored client-side, and read back early enough to avoid a flash."""
        switch = self._switch()
        switch.click()
        self.wait_until(lambda: self._stamped_theme() == settings.BRAND_THEME_DARK)

        self.browser.get(self.server_url + reverse("faq"))

        self.wait_until(lambda: self._stamped_theme() == settings.BRAND_THEME_DARK)

    def test_the_switch_says_which_state_it_is_in(self):
        """`aria-pressed` is the only cue a screen reader gets from an icon."""
        switch = self._switch()
        self.assertEqual(switch.get_attribute("aria-pressed"), "false")

        switch.click()
        self.wait_until(lambda: switch.get_attribute("aria-pressed") == "true")

    def test_a_signed_out_reader_is_not_offered_the_appearance_page(self):
        """Customize leads somewhere they cannot go; it must not be shown."""
        self.browser.get(self.server_url + reverse("disclaimer"))

        self.assertFalse(
            self.browser.find_elements(
                By.CSS_SELECTOR, f'a[href="{reverse("profile_appearance")}"]'
            )
        )


class AppearancePageTest(FunctionalTest):
    """The appearance page behind Customize."""

    def _open(self, email="appearance@example.com"):
        self.create_cookie_and_go_to_index_page(email)
        self.browser.get(self.server_url + reverse("profile_appearance"))

    def _stamped_theme(self):
        return self.browser.find_element(By.TAG_NAME, "html").get_attribute(
            "data-theme"
        )

    def test_a_signed_out_reader_is_sent_to_log_in(self):
        self.browser.get(self.server_url + reverse("profile_appearance"))

        self.assertIn("/accounts/login/", self.browser.current_url)

    def test_customize_in_the_header_leads_here(self):
        """The dropdown's first entry is the way in, so it has to arrive."""
        self.create_cookie_and_go_to_index_page("customize@example.com")
        self.browser.get(self.server_url + reverse("disclaimer"))
        self.browser.execute_script(
            "document.querySelector('#id-theme-list').closest('details').open = true;"
        )

        self.browser.find_element(
            By.CSS_SELECTOR, f'#id-theme-list a[href="{reverse("profile_appearance")}"]'
        ).click()

        self.wait_until(
            lambda: reverse("profile_appearance") in self.browser.current_url
        )

    def test_every_offered_theme_has_a_swatch_that_renders_in_itself(self):
        """The page exists so the choice can be made by looking.

        Without `data-theme` on each swatch they would all render in the
        current theme and look identical -- which is the flat list of names
        this page replaces.
        """
        self._open()

        for theme in settings.AVAILABLE_THEMES:
            with self.subTest(theme=theme):
                self.assertTrue(
                    self.browser.find_elements(
                        By.CSS_SELECTOR, f'label[data-theme="{theme}"]'
                    ),
                    f"{theme} has no swatch previewing itself",
                )

    def test_choosing_a_theme_applies_it_immediately(self):
        self._open()
        target = self.browser.find_element(
            By.CSS_SELECTOR, 'input[name="theme-dropdown"][value="abyss"]'
        )
        self.browser.execute_script(
            "arguments[0].checked = true;"
            "arguments[0].dispatchEvent(new Event('change'));",
            target,
        )

        self.wait_until(lambda: self._stamped_theme() == "abyss")

    def test_a_theme_chosen_here_survives_a_page_change(self):
        """Same storage as the header control, so the two cannot disagree."""
        self._open()
        target = self.browser.find_element(
            By.CSS_SELECTOR, 'input[name="theme-dropdown"][value="nord"]'
        )
        self.browser.execute_script(
            "arguments[0].checked = true;"
            "arguments[0].dispatchEvent(new Event('change'));",
            target,
        )
        self.wait_until(lambda: self._stamped_theme() == "nord")

        self.browser.get(self.server_url + reverse("faq"))

        self.wait_until(lambda: self._stamped_theme() == "nord")

    def test_the_page_is_marked_on_the_profile_sub_nav(self):
        """The reader has to be able to tell where they are."""
        self._open()

        marked = self.browser.find_elements(
            By.CSS_SELECTOR, 'nav[aria-label="Profile sections"] [aria-current="page"]'
        )
        self.assertEqual([m.text for m in marked], ["Appearance"])

    def test_the_third_party_themes_are_credited_on_the_page(self):
        """CC BY attribution has to appear wherever the themes are offered."""
        self._open()
        body = self.browser.find_element(By.TAG_NAME, "body").text

        self.assertIn(settings.THEME_ATTRIBUTION["author"], body)
        self.assertIn(settings.THEME_ATTRIBUTION["license"], body)


class AppearanceTypefaceTest(FunctionalTest):
    """The typeface picker, and the tier that guards it.

    Choosing a theme is free to any signed-in reader; borrowing another theme's
    typeface pairing is an Asastatser feature. Below the tier the choices are
    still rendered -- disabled, inside a link to subscriptions -- so the reader
    can see what the upgrade buys, the way the explorer preference does.
    """

    def _open(self, email, permission):
        self.create_cookie_and_go_to_index_page_tier(email, permission=permission)
        self.browser.get(self.server_url + reverse("profile_appearance"))

    def _entitled(self):
        self._open(
            "typeface-paid@example.com",
            SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
        )

    def _unentitled(self):
        self._open(
            "typeface-free@example.com",
            SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"] - 1,
        )

    def _stamped_typeface(self):
        return self.browser.find_element(By.TAG_NAME, "html").get_attribute(
            "data-typeface"
        )

    def _choose(self, value):
        target = self.browser.find_element(
            By.CSS_SELECTOR, f'input[name="typeface-choice"][value="{value}"]'
        )
        self.browser.execute_script(
            "arguments[0].checked = true;"
            "arguments[0].dispatchEvent(new Event('change'));",
            target,
        )

    def test_an_entitled_reader_can_choose_a_pairing(self):
        self._entitled()

        self._choose("rosepine")

        self.wait_until(lambda: self._stamped_typeface() == "rosepine")

    def test_the_choice_survives_a_page_change(self):
        """Stamped in the head before paint, like the theme."""
        self._entitled()
        self._choose("nord")
        self.wait_until(lambda: self._stamped_typeface() == "nord")

        self.browser.get(self.server_url + reverse("faq"))

        self.wait_until(lambda: self._stamped_typeface() == "nord")

    def test_theme_default_clears_the_override(self):
        """The empty choice returns the reader to their theme's own pairing."""
        self._entitled()
        self._choose("nord")
        self.wait_until(lambda: self._stamped_typeface() == "nord")

        self._choose("")

        self.wait_until(lambda: self._stamped_typeface() is None)

    def test_the_typeface_is_independent_of_the_theme(self):
        """Two axes: choosing a theme must not disturb a chosen pairing."""
        self._entitled()
        self._choose("nord")
        self.wait_until(lambda: self._stamped_typeface() == "nord")

        theme = self.browser.find_element(
            By.CSS_SELECTOR, 'input[name="theme-dropdown"][value="abyss"]'
        )
        self.browser.execute_script(
            "arguments[0].checked = true;"
            "arguments[0].dispatchEvent(new Event('change'));",
            theme,
        )

        self.wait_until(
            lambda: self.browser.find_element(
                By.TAG_NAME, "html"
            ).get_attribute("data-theme") == "abyss"
        )
        self.assertEqual(self._stamped_typeface(), "nord")

    def test_an_unentitled_reader_sees_the_choices_but_cannot_use_them(self):
        self._unentitled()

        inputs = self.browser.find_elements(
            By.CSS_SELECTOR, 'input[name="typeface-choice"]'
        )
        self.assertTrue(inputs, "the pairings were hidden rather than disabled")
        self.assertTrue(
            all(i.get_attribute("disabled") for i in inputs),
            "a pairing was left usable below the tier",
        )

    def test_an_unentitled_reader_is_pointed_at_subscriptions(self):
        self._unentitled()

        link = self.browser.find_element(
            By.CSS_SELECTOR, f'#id-section-typeface a[href="{reverse("subscriptions")}"]'
        )
        self.assertIn("Asastatser", link.get_attribute("title"))

    def test_an_unentitled_reader_can_still_choose_a_theme(self):
        """The tier buys typefaces, not themes."""
        self._unentitled()

        theme = self.browser.find_element(
            By.CSS_SELECTOR, 'input[name="theme-dropdown"][value="nord"]'
        )
        self.assertIsNone(theme.get_attribute("disabled"))
        self.browser.execute_script(
            "arguments[0].checked = true;"
            "arguments[0].dispatchEvent(new Event('change'));",
            theme,
        )

        self.wait_until(
            lambda: self.browser.find_element(
                By.TAG_NAME, "html"
            ).get_attribute("data-theme") == "nord"
        )

