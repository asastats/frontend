"""Functional tests for home and the bundle-name forms, rebuilt 2026-08-22.

These pages were the last of the redesign. The framework migration had reached
them; the design pass had not. What that left, and what these tests pin:

* a four-column shell whose rail held one box printing the reader's email three
  times, with three-quarters of the column empty;
* every line centred, so a column of bundle names of different widths had no
  edge to scan down;
* each bundle rendered as **four links to three destinations** with nothing to
  tell them apart -- the name evaluated it, a line beneath opened the historic
  widget, and the whole box below was a fourth link to the edit form;
* `<br><br>` for spacing, and the four-colour message badge that had already
  been fixed on three other pages.

Two faults found while rebuilding, both of which only a browser shows:

* **`home.js` filtered on a constant.** `changeFiltering` matched
  `$(this).children().children().attr('title')`, which is the literal string
  "Evaluate bundle" on every row -- so typing "eval" revealed the whole list
  and the attribute matched nothing anybody would search for. It also tied the
  filter to how deeply the row happened to be nested.
* **`#id_panel { padding: 0 }`** sat in the shared stylesheet from the old
  design. An id selector outranks a utility class, so the rebuilt panel's
  padding was silently dropped and its controls ran past both edges of the card
  they sit in. Nothing about the markup was wrong; only the rendered page said
  so.
"""

from django.urls import reverse
from selenium.webdriver.common.by import By
from utils.tests.fixtures import TEST_ADDRESS, TEST_ADDRESS2, TEST_ADDRESS3

from .base import FunctionalTest

#: A tier that clears every gate on these pages, so nothing here is testing
#: entitlement by accident.
PROFESSIONAL = 258_885_438_200


class HomePageTest(FunctionalTest):
    """What a reader sees, and what they can press."""

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_bundlename_add_page(
            "home@example.com", permission=PROFESSIONAL
        )

    def add(self, name, addresses):
        self.browser.get(self.server_url + "/profile/add-bundle")
        self.sleep()
        self.submit_bundlename_name(name, addresses)
        self.sleep()

    def add_three(self):
        self.add("Long term holdings", f"{TEST_ADDRESS} {TEST_ADDRESS2}")
        self.add("Trading", f"{TEST_ADDRESS2} {TEST_ADDRESS3}")
        self.add("Cold storage", TEST_ADDRESS)

    def open_home(self):
        self.record_javascript_errors()
        self.browser.get(self.server_url + reverse("home"))
        self.sleep()

    def rows(self):
        """The bundle rows a reader can see."""
        return [
            row
            for row in self.browser.find_elements(By.CSS_SELECTOR, ".cardiv")
            if row.is_displayed()
        ]

    # -- the shell ----------------------------------------------------------

    def test_the_page_has_no_rail_to_leave_empty(self):
        """One centred column, the answer the profile section reached first.

        The rail carried right-aligned breadcrumbs and a box repeating the
        reader's email; on a page whose content is a list, it was three-quarters
        of a column of nothing.
        """
        self.open_home()

        self.assertFalse(self.browser.find_elements(By.TAG_NAME, "aside"))
        self.assertEqual(
            "Your bundles",
            self.browser.find_element(By.CSS_SELECTOR, "main h1").text,
        )

    def test_the_account_is_named_once_and_leads_to_the_profile(self):
        """It was printed three times: `profile.name`, `username`, `email`.

        On an account that signed up with an email -- which is all of them --
        those are the same string.
        """
        self.open_home()

        page = self.browser.find_element(By.TAG_NAME, "main").text
        self.assertEqual(1, page.count("home@example.com"))

        profile = self.browser.find_element(By.ID, "id_profile")
        self.assertIn(reverse("profile"), profile.get_attribute("href"))

    def test_a_reader_with_no_bundles_is_told_what_one_is(self):
        """The old page rendered a heading, a gap and a button."""
        self.open_home()

        self.assertIn("No bundles yet", self.browser.find_element(By.TAG_NAME, "main").text)
        self.assertTrue(self.browser.find_elements(By.ID, "id_add"))

    # -- the rows -----------------------------------------------------------

    def test_a_bundle_row_says_where_each_control_goes(self):
        """Four links to three destinations became one link and two buttons.

        The name evaluates -- that is what a reader came for -- and the other
        two destinations are named. Nothing else in the row is clickable, so
        there is no longer a box whose entire area is a link to somewhere the
        reader cannot guess.
        """
        self.add("Long term holdings", f"{TEST_ADDRESS} {TEST_ADDRESS2}")
        self.open_home()

        row = self.rows()[0]
        links = row.find_elements(By.TAG_NAME, "a")
        labels = [link.text.strip() for link in links]

        self.assertIn("Long-term-holdings", labels)
        self.assertIn("Edit", labels)
        self.assertIn("Historic", labels)
        # Three destinations, three controls -- not four controls for three.
        self.assertEqual(3, len(links))

        # Three different places. The evaluation is at the site root, the edit
        # form under /profile/, the widget under /historic/ -- so a reader who
        # cannot tell the controls apart cannot guess where any of them goes.
        destinations = {link.text.strip(): link.get_attribute("href") for link in links}
        self.assertRegex(destinations["Long-term-holdings"], r"/Long-term-holdings$")
        self.assertIn("/profile/Long-term-holdings/", destinations["Edit"])
        self.assertIn("/historic/", destinations["Historic"])
        self.assertEqual(3, len(set(destinations.values())))

    def test_the_address_count_is_said_rather_than_shown(self):
        """It was a bare number in a badge in the corner, which reads as an
        index or a notification rather than as a count of addresses."""
        self.add("Long term holdings", f"{TEST_ADDRESS} {TEST_ADDRESS2}")
        self.add("Cold storage", TEST_ADDRESS)
        self.open_home()

        text = " ".join(row.text for row in self.rows())
        self.assertIn("2 addresses", text)
        self.assertIn("1 address", text)

    def test_every_row_carries_the_keys_the_sorter_reads(self):
        """`.cardiv` as a **direct div child** of `.bundlenames`, with its keys.

        The sorter does `$(".bundlenames").html($(this).children("div").sort())`,
        so a wrapper between the two would leave it sorting one element and
        silently doing nothing.
        """
        self.add_three()
        self.open_home()

        direct = self.browser.find_elements(By.CSS_SELECTOR, ".bundlenames > div.cardiv")
        self.assertEqual(3, len(direct))
        for row in direct:
            with self.subTest(row=row.get_attribute("data-name")):
                for key in ("name", "addresses", "created", "modified", "size"):
                    self.assertTrue(
                        row.get_attribute(f"data-{key}"),
                        f"data-{key} is missing, so sorting by it does nothing",
                    )

    # -- sorting and filtering ----------------------------------------------

    def test_the_panel_is_absent_until_there_is_something_to_sort(self):
        self.add("Only one", TEST_ADDRESS)
        self.open_home()

        self.assertFalse(self.browser.find_elements(By.ID, "id_panel"))

    def test_the_panel_fits_inside_the_card_it_sits_in(self):
        """Measured, because this failed while looking perfectly correct.

        `#id_panel { padding: 0 }` survived in the stylesheet from the old
        design, and an id selector outranks the utility classes that replaced
        it -- so the controls ran past both edges of their card and the Sort
        label was clipped by the viewport.
        """
        self.add_three()
        self.open_home()

        panel = self.browser.find_element(By.ID, "id_panel")
        card = panel.find_element(By.XPATH, "./ancestor::section")

        panel_box = self.browser.execute_script(
            "var r = arguments[0].getBoundingClientRect();"
            "return {left: r.left, right: r.right};",
            panel,
        )
        card_box = self.browser.execute_script(
            "var r = arguments[0].getBoundingClientRect();"
            "return {left: r.left, right: r.right};",
            card,
        )
        self.assertGreaterEqual(panel_box["left"], card_box["left"])
        self.assertLessEqual(panel_box["right"], card_box["right"])

        # And every control inside it, which is what actually overflowed.
        for control in panel.find_elements(By.CSS_SELECTOR, "label, div[role=group]"):
            with self.subTest(control=control.get_attribute("class")[:30]):
                box = self.browser.execute_script(
                    "var r = arguments[0].getBoundingClientRect();"
                    "return {left: r.left, right: r.right};",
                    control,
                )
                self.assertGreaterEqual(round(box["left"]), round(card_box["left"]))
                self.assertLessEqual(round(box["right"]), round(card_box["right"]))

    def test_the_sort_control_shows_which_option_is_on(self):
        """A segmented control, the idiom the rest of the site uses.

        It was two fieldsets, the second pushed down five units so its two rows
        never lined up with the first's. The radios are still radios -- arrow
        keys move between them -- and `sr-only` rather than `hidden` keeps them
        focusable.
        """
        self.add_three()
        self.open_home()

        name = self.browser.find_element(By.ID, "id_name")
        size = self.browser.find_element(By.ID, "id_size")
        self.assertTrue(name.is_selected())

        lifted = self._background(name)
        self.assertNotEqual(
            lifted,
            self._background(size),
            "the chosen sort looks exactly like the ones that are off",
        )

        size.find_element(By.XPATH, "..").click()

        self.wait_until(lambda: size.is_selected())
        self.assertEqual(lifted, self._background(size))

    def _background(self, radio):
        """The background of the label wrapping a visually hidden input."""
        return self.browser.execute_script(
            "return getComputedStyle(arguments[0].parentElement).backgroundColor;",
            radio,
        )

    def test_sorting_reorders_the_rows(self):
        self.add_three()
        self.open_home()
        by_name = [row.get_attribute("data-name") for row in self.rows()]
        self.assertEqual(sorted(by_name), by_name)

        self.browser.find_element(By.ID, "id_size").find_element(By.XPATH, "..").click()

        self.wait_until(
            lambda: [row.get_attribute("data-size") for row in self.rows()]
            == sorted(row.get_attribute("data-size") for row in self.rows())
        )

    def test_descending_reverses_them(self):
        self.add_three()
        self.open_home()
        first = self.rows()[0].get_attribute("data-name")

        self.browser.find_element(By.ID, "id_desc").find_element(By.XPATH, "..").click()

        self.wait_until(lambda: self.rows()[0].get_attribute("data-name") != first)

    def test_filtering_matches_a_name(self):
        self.add_three()
        self.open_home()

        self.browser.find_element(By.ID, "id_filter").send_keys("cold")

        self.wait_until(lambda: len(self.rows()) == 1)
        self.assertEqual("Cold-storage", self.rows()[0].get_attribute("data-name"))

    def test_filtering_matches_an_address(self):
        """The placeholder says name or address, so it has to do both."""
        self.add_three()
        self.open_home()

        self.browser.find_element(By.ID, "id_filter").send_keys(TEST_ADDRESS3[:12])

        self.wait_until(lambda: len(self.rows()) == 1)
        self.assertEqual("Trading", self.rows()[0].get_attribute("data-name"))

    def test_filtering_no_longer_matches_the_word_evaluate(self):
        """The bug this rebuild found.

        `changeFiltering` read `$(this).children().children().attr('title')`,
        which was "Evaluate bundle" on every row -- so this query showed the
        whole list, and no query a reader would type ever matched that pass.
        """
        self.add_three()
        self.open_home()

        self.browser.find_element(By.ID, "id_filter").send_keys("eval")

        self.wait_until(lambda: len(self.rows()) == 0)

    def test_clearing_the_filter_brings_every_row_back(self):
        self.add_three()
        self.open_home()
        field = self.browser.find_element(By.ID, "id_filter")
        field.send_keys("cold")
        self.wait_until(lambda: len(self.rows()) == 1)

        field.clear()
        field.send_keys(" ")
        field.send_keys("\b")

        self.wait_until(lambda: len(self.rows()) == 3)
        self.assertEqual([], self.javascript_errors())


class BundleNameFormTest(FunctionalTest):
    """The three forms: add, edit and delete."""

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_bundlename_add_page(
            "forms@example.com", permission=PROFESSIONAL
        )

    def add(self, name, addresses):
        self.browser.get(self.server_url + "/profile/add-bundle")
        self.sleep()
        self.submit_bundlename_name(name, addresses)
        self.sleep()

    def open_edit(self, name):
        self.browser.get(self.server_url + reverse("home"))
        self.sleep()
        link = [
            a
            for a in self.browser.find_elements(By.CSS_SELECTOR, ".cardiv a")
            if a.text.strip() == "Edit"
            and name.replace(" ", "-") in a.get_attribute("href")
        ][0]
        link.click()
        self.sleep()

    def test_the_actions_sit_with_the_fields_they_act_on(self):
        """Save was a third of a page to the right of the last field.

        Measured: the submit control has to be *below* the fields now, in the
        footer of the card holding them, rather than in a column beside them.
        """
        self.browser.get(self.server_url + "/profile/add-bundle")
        self.sleep()

        addresses = self.browser.find_element(By.ID, "id_addresses")
        submit = self.browser.find_element(By.ID, "id_submit")

        self.assertGreater(
            submit.location["y"],
            addresses.location["y"] + addresses.size["height"] - 1,
            "the submit control is level with the fields rather than after them",
        )

    def test_one_control_reads_as_the_primary_one(self):
        """Save and Back were the same weight, so neither was the answer."""
        self.browser.get(self.server_url + "/profile/add-bundle")
        self.sleep()

        primaries = [
            button.text.strip()
            for button in self.browser.find_elements(By.CSS_SELECTOR, "main .btn-primary")
        ]

        self.assertEqual(["Save"], primaries)

    def test_the_address_box_is_sized_for_what_it_holds(self):
        """It was twenty rows -- taller than the rest of the form together.

        `field-sizing: content` makes `rows` a minimum, so it grows with what
        is pasted in; twenty as the minimum meant a one-address bundle got a
        box the size of the page.
        """
        self.browser.get(self.server_url + "/profile/add-bundle")
        self.sleep()

        addresses = self.browser.find_element(By.ID, "id_addresses")
        name = self.browser.find_element(By.ID, "id_name")

        self.assertLess(addresses.size["height"], 200)
        # And the two fields read as the same kind of control, which a
        # browser-default text box beside a full-width textarea does not.
        self.assertAlmostEqual(
            name.size["width"], addresses.size["width"], delta=4
        )

    def test_the_edit_page_offers_deletion_as_a_marked_step(self):
        """It was a red link three lines under Save.

        The same treatment the account page gives deactivation: its own
        section, marked, at the end -- findable without being the next thing
        the eye lands on.
        """
        self.add("Cold storage", TEST_ADDRESS)
        self.open_edit("Cold storage")

        delete = self.browser.find_element(By.ID, "id_delete")
        submit = self.browser.find_element(By.ID, "id_submit")

        self.assertGreater(delete.location["y"], submit.location["y"])
        self.assertIn("btn-error", delete.get_attribute("class"))
        self.assertIn("/delete", delete.get_attribute("href"))

    def test_the_edit_page_says_when_it_was_made_and_touched(self):
        self.add("Cold storage", TEST_ADDRESS)
        self.open_edit("Cold storage")

        self.assertTrue(self.browser.find_element(By.ID, "id_created").text.strip())
        self.assertTrue(self.browser.find_element(By.ID, "id_modified").text.strip())

    def test_the_sibling_list_marks_where_the_reader_is(self):
        """Half of what sibling navigation is for.

        It was a rail; it is a card now, and the current entry carries
        `aria-current="page"` so the state is announced as well as painted.
        """
        self.add("Cold storage", TEST_ADDRESS)
        self.add("Trading", TEST_ADDRESS2)
        self.open_edit("Cold storage")

        current = self.browser.find_elements(By.CSS_SELECTOR, '[aria-current="page"]')
        named = [
            element.text.strip()
            for element in current
            if "Cold-storage" in element.text
        ]
        self.assertTrue(named, "no entry in the sibling list is marked as the current one")

    def test_the_sibling_list_is_absent_when_there_is_nowhere_to_go(self):
        self.add("Only one", TEST_ADDRESS)
        self.open_edit("Only one")

        self.assertNotIn("Your bundles", self.browser.find_element(By.TAG_NAME, "main").text)

    def test_deleting_asks_first_and_says_what_survives(self):
        """The one page whose whole purpose is to stop and ask."""
        self.add("Cold storage", TEST_ADDRESS)
        self.open_edit("Cold storage")

        self.browser.find_element(By.ID, "id_delete").click()
        self.sleep()

        alert = self.browser.find_element(By.CSS_SELECTOR, '[role="alert"]')
        self.assertIn("cannot be undone", alert.text)
        # What is actually lost, rather than only that something is.
        self.assertIn(
            "addresses stay on the chain",
            self.browser.find_element(By.TAG_NAME, "main").text,
        )
        self.assertIn(
            "btn-error",
            self.browser.find_element(By.ID, "id_submit").get_attribute("class"),
        )
