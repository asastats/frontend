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
        edit. core.tests.test_context_processors keeps those two in step.

        Twelve, not all 57: a dropdown is for choosing and the appearance page
        is for browsing. A fresh browser has used nothing, so the Recent group
        is empty and these are all there is.
        """
        radios = self._open_picker()
        self.assertEqual(
            [r.get_attribute("value") for r in radios],
            list(settings.DEFAULT_THEMES),
        )

    def test_picker_links_to_the_rest(self):
        """The other 45 have to be reachable from here, or they are lost."""
        self._open_picker()

        links = self.browser.find_elements(
            By.CSS_SELECTOR,
            f'#id-theme-list a[href="{reverse("profile_appearance")}"]',
        )

        self.assertTrue(links, "the dropdown offers no way to the full set")

    def test_no_theme_is_stamped_until_one_is_chosen(self):
        self.create_cookie_and_go_to_index_page("unstamped@example.com")
        self.browser.get(self.server_url + reverse("disclaimer"))
        # Unstamped means DaisyUI's own default applies -- the `asastats` theme
        # is registered with `default: true`, so the page is still branded.
        self.assertIsNone(self._stamped_theme())

    def test_choosing_a_theme_applies_it_and_survives_a_page_change(self):
        radios = self._open_picker()
        target = next(r for r in radios if r.get_attribute("value") == "dracula")
        self.browser.execute_script(
            "arguments[0].checked = true;"
            "arguments[0].dispatchEvent(new Event('change'));",
            target,
        )
        self.wait_until(lambda: self._stamped_theme() == "dracula")

        # The choice is client-side only, so it has to come back from storage,
        # and early enough that the page never paints the default first.
        self.browser.get(self.server_url + reverse("faq"))
        self.wait_until(lambda: self._stamped_theme() == "dracula")

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

    def test_an_unentitled_reader_gets_no_dead_controls(self):
        """The Fonts tab is a link below the tier, not a panel of dead radios.

        Rendering every pairing disabled read as a control that had broken
        rather than one that has a price.
        """
        self._unentitled()

        self.assertFalse(
            self.browser.find_elements(
                By.CSS_SELECTOR, 'input[name="typeface-choice"]'
            ),
            "a typeface control was rendered below the tier",
        )

    def test_an_unentitled_reader_is_pointed_at_subscriptions(self):
        self._unentitled()

        tab = self.browser.find_element(By.CSS_SELECTOR, "#id-tab-fonts")

        self.assertEqual(tab.tag_name, "a")
        self.assertEqual(
            tab.get_attribute("href").split(self.live_server_url)[-1],
            reverse("subscriptions"),
        )
        self.assertIn("Asastatser", tab.get_attribute("title"))

    def test_an_entitled_reader_gets_fonts_as_a_tab(self):
        """Above the tier it is a tab like Dark and Light, not a link away."""
        self._entitled()

        tab = self.browser.find_element(By.CSS_SELECTOR, "#id-tab-fonts")

        self.assertEqual(tab.tag_name, "input")
        self.assertEqual(tab.get_attribute("name"), "appearance-tab")

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


class AppearanceRecentThemesTest(FunctionalTest):
    """The dropdown promotes what this browser has actually used.

    The tally is localStorage only, like the theme it ranks. A tally that
    synced while the theme did not would order the menu by a history this
    browser never had -- so both live in the same place, and clearing site data
    clears both together.

    A theme counts when it survives a navigation, not when it is clicked. That
    is the difference between choosing one and browsing the appearance page,
    where every click applies a theme for a moment.
    """

    def _sign_in(self):
        self.create_cookie_and_go_to_index_page("recent@example.com")

    def _open_picker(self, page="disclaimer"):
        self.browser.get(self.server_url + reverse(page))
        self.browser.execute_script(
            "document.querySelector('#id-theme-list').closest('details').open = true;"
        )

    def _choose(self, theme):
        self.browser.execute_script(
            "var r = document.querySelector("
            "  \'#id-theme-list input[value=\"' + arguments[0] + '\"]\');"
            "r.checked = true; r.dispatchEvent(new Event('change'));",
            theme,
        )

    def _recent(self):
        return [
            el.get_attribute("value")
            for el in self.browser.find_elements(
                By.CSS_SELECTOR, "#id-theme-list [data-theme-recent] input"
            )
        ]

    def _usage(self):
        return self.browser.execute_script(
            "return JSON.parse(localStorage.getItem('themeUsage') || '{}');"
        )

    def test_a_fresh_browser_has_no_recent_group(self):
        self._sign_in()

        self._open_picker()

        self.assertEqual(self._recent(), [])
        self.assertTrue(
            self.browser.find_element(
                By.CSS_SELECTOR, "#id-theme-recent-title"
            ).get_attribute("hidden")
        )

    def test_a_chosen_theme_is_counted_once_it_survives_a_page(self):
        self._sign_in()
        self._open_picker()

        self._choose("dracula")
        self.wait_until(
            lambda: self.browser.find_element(
                By.TAG_NAME, "html"
            ).get_attribute("data-theme") == "dracula"
        )
        # Not counted yet: nothing has been navigated away from.
        self.assertEqual(self._usage(), {})

        self._open_picker("faq")

        self.assertEqual(self._usage(), {"dracula": 1})

    def test_a_used_theme_leads_the_dropdown(self):
        self._sign_in()
        self._open_picker()
        self._choose("gruvbox")
        self.wait_until(
            lambda: self.browser.find_element(
                By.TAG_NAME, "html"
            ).get_attribute("data-theme") == "gruvbox"
        )

        self._open_picker("faq")

        self.assertEqual(self._recent(), ["gruvbox"])

    def test_a_promoted_theme_is_not_offered_twice(self):
        """Two radios sharing a name and a value fight over which is chosen."""
        self._sign_in()
        self._open_picker()
        self._choose("mocha")
        self.wait_until(
            lambda: self.browser.find_element(
                By.TAG_NAME, "html"
            ).get_attribute("data-theme") == "mocha"
        )

        self._open_picker("faq")

        self.assertEqual(
            len(
                self.browser.find_elements(
                    By.CSS_SELECTOR,
                    "#id-theme-list input[name='theme-dropdown'][value='mocha']",
                )
            ),
            1,
        )

    def test_browsing_more_pages_does_not_inflate_the_count(self):
        """The count means chosen and kept, not page views."""
        self._sign_in()
        self._open_picker()
        self._choose("tokyonight")
        self.wait_until(
            lambda: self.browser.find_element(
                By.TAG_NAME, "html"
            ).get_attribute("data-theme") == "tokyonight"
        )

        self._open_picker("faq")
        self._open_picker("disclaimer")
        self._open_picker("faq")

        self.assertEqual(self._usage(), {"tokyonight": 1})

    def test_a_promoted_theme_still_applies_when_chosen(self):
        """A cloned entry that does nothing when clicked is worse than none."""
        self._sign_in()
        self._open_picker()
        self._choose("dracula")
        self.wait_until(
            lambda: self.browser.find_element(
                By.TAG_NAME, "html"
            ).get_attribute("data-theme") == "dracula"
        )
        self._open_picker("faq")
        self._choose("asastats")
        self.wait_until(
            lambda: self.browser.find_element(
                By.TAG_NAME, "html"
            ).get_attribute("data-theme") == "asastats"
        )

        self._open_picker("disclaimer")
        self._choose("dracula")

        self.wait_until(
            lambda: self.browser.find_element(
                By.TAG_NAME, "html"
            ).get_attribute("data-theme") == "dracula"
        )


class AppearanceTabsTest(FunctionalTest):
    """The tabs must look like every other tablist on the site.

    The swap modal's segmented control is the design the site follows, and the
    login modal and the profile sub-nav already match it: a sunken tray, equal
    columns, and the selected tab lifting out of it on the surface colour with
    a shadow. This page used DaisyUI's `tabs-lift` -- folder tabs -- which was
    the one control that did not.

    Asserted through computed style rather than class names, because the point
    is what a reader sees; a refactor that keeps the look is free to change how
    it gets there.
    """

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_index_page_tier(
            "tabs@example.com", permission=100
        )
        self.browser.get(self.server_url + reverse("profile_appearance"))

    def _bg(self, element):
        return self.browser.execute_script(
            "return getComputedStyle(arguments[0]).backgroundColor;", element
        )

    def test_the_selected_tab_lifts_out_of_the_tray(self):
        tray = self.browser.find_element(By.ID, "id-appearance-tabs")
        selected = self.browser.find_element(By.ID, "id-tab-light")
        unselected = self.browser.find_element(By.ID, "id-tab-dark")

        self.assertNotEqual(
            self._bg(selected), self._bg(tray), "the selected tab does not stand out"
        )
        self.assertEqual(
            self._bg(unselected),
            "rgba(0, 0, 0, 0)",
            "an unselected tab is painted; only the selected one should be",
        )

    def test_the_tray_matches_the_profile_sub_nav(self):
        """One idiom for the whole site, not one per page.

        The sub-nav sits on this very page, directly above these tabs, so a
        mismatch is visible in a single glance -- and it is the same control
        the login modal and the swap modal use.
        """
        tray = self.browser.find_element(By.ID, "id-appearance-tabs")
        sub_nav = self.browser.find_element(
            By.CSS_SELECTOR, '[aria-label="Profile sections"]'
        )

        self.assertEqual(self._bg(tray), self._bg(sub_nav))

    def test_the_tray_matches_the_login_modal(self):
        """The same, across pages and across signed-in state.

        The modal renders only for a signed-out reader, so the session is
        dropped first -- which is also the only way to see the control this
        page was supposed to copy.
        """
        tray_bg = self._bg(self.browser.find_element(By.ID, "id-appearance-tabs"))

        self.browser.delete_all_cookies()
        self.browser.get(self.server_url + reverse("about"))
        modal_tray = self.browser.find_elements(
            By.CSS_SELECTOR, '#modalLogin [role="tablist"]'
        )

        self.assertTrue(modal_tray, "the login modal renders no tablist")
        self.assertEqual(tray_bg, self._bg(modal_tray[0]))

    def test_the_tabs_share_the_row_evenly(self):
        widths = [
            tab.size["width"]
            for tab in self.browser.find_elements(
                By.CSS_SELECTOR, "#id-appearance-tabs > .tab"
            )
        ]

        self.assertEqual(len(widths), 3)
        self.assertLess(max(widths) - min(widths), 2, f"tabs are uneven: {widths}")

    def test_choosing_a_tab_swaps_the_panel_without_scripting(self):
        dark = self.browser.find_element(By.ID, "id-tab-dark")
        self.browser.execute_script("arguments[0].click();", dark)

        panels = self.browser.find_elements(By.CSS_SELECTOR, "#id-appearance-tabs > .tab-content")
        shown = [p for p in panels if p.is_displayed()]

        self.assertEqual(len(shown), 1, "exactly one panel should be visible")
        self.assertTrue(
            shown[0].find_elements(
                By.CSS_SELECTOR, "input[value='asastats-dark']"
            ),
            "the Dark tab did not reveal the dark themes",
        )

    def test_light_leads_the_tabs(self):
        """The header dropdown lists Light before Dark; this must agree."""
        tabs = self.browser.find_elements(
            By.CSS_SELECTOR, "#id-appearance-tabs > .tab"
        )

        # Below the Asastatser tier Fonts is a link rather than a radio, so it
        # carries its name as text instead of an aria-label. Either is the
        # accessible name; the order is what this pins.
        names = [
            (t.get_attribute("aria-label") or t.text).split()[0] for t in tabs
        ]

        self.assertEqual(names, ["Light", "Dark", "Fonts"])
