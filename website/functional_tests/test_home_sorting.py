from datetime import datetime

from selenium.webdriver.common.by import By

from utils.tests.fixtures import TEST_ADDRESS, TEST_ADDRESS2, TEST_ADDRESS3

from .base import FunctionalTest


class HomeSortingAndFilteringTest(FunctionalTest):
    def test_home_bundlename_cards_data_attributes(self):
        # Dieter signs up
        self.create_cookie_and_go_to_bundlename_add_page(
            "dieter_pro@example.com", permission=258_885_438_200
        )

        # He adds two bundlenames
        bundlename1 = "Bundle name 1"
        self.submit_bundlename_name(bundlename1, f"{TEST_ADDRESS} {TEST_ADDRESS2}")
        self.browser.get(self.server_url + "/profile/add-bundle")
        self.sleep()
        bundlename2 = "Bundle name 2"
        self.submit_bundlename_name(bundlename2, f"{TEST_ADDRESS2} {TEST_ADDRESS3}")
        self.sleep()
        self.browser.get(self.server_url + "/home/")
        self.sleep()
        now = datetime.now()
        date_format = "%Y-%m-%d %H:%M:%S"
        cards = self.browser.find_elements(By.CLASS_NAME, "cardiv")

        self.assertEqual(
            sorted(cards[0].get_attribute("data-addresses").split(" ")),
            sorted(f"{TEST_ADDRESS} {TEST_ADDRESS2}".split(" ")),
        )
        self.assertEqual(
            sorted(cards[1].get_attribute("data-addresses").split(" ")),
            sorted(f"{TEST_ADDRESS2} {TEST_ADDRESS3}".split(" ")),
        )
        self.assertEqual(cards[0].get_attribute("data-name"), "Bundle-name-1")
        self.assertEqual(cards[1].get_attribute("data-name"), "Bundle-name-2")
        for card in cards:
            created = datetime.strptime(card.get_attribute("data-created"), date_format)
            modified = datetime.strptime(
                card.get_attribute("data-modified"), date_format
            )
            self.assertGreaterEqual(modified, created)
            self.assertGreaterEqual(now, created)
            self.assertGreaterEqual(now, modified)

    def test_home_bundlename_sorting_bundlenames(self):
        # Mario signs up
        self.create_cookie_and_go_to_bundlename_add_page(
            "mario_pro@example.com", permission=258_885_438_200
        )

        # He adds a bundlename
        bundlename1 = "Bundle first"
        self.submit_bundlename_name(bundlename1, f"{TEST_ADDRESS} {TEST_ADDRESS2}")
        self.browser.get(self.server_url + "/home/")
        self.sleep()
        # He sees no panel
        panel = self.browser.find_elements(By.ID, "id_panel")
        self.assertEqual(len(panel), 0)

        self.browser.get(self.server_url + "/profile/add-bundle")
        self.sleep()
        bundlename2 = "Bundle abc"
        self.submit_bundlename_name(bundlename2, f"{TEST_ADDRESS2} {TEST_ADDRESS2}")
        self.sleep()
        self.browser.get(self.server_url + "/home/")
        self.sleep()

        # He sees abc bundlename is the first
        cards = self.find_elems_by_class("cardiv")
        self.assertEqual(cards[0].get_attribute("data-name"), "Bundle-abc")

        # He sees panel now
        panel = self.find_elem_by_id("id_panel")

        # And sort by addresses is selected
        radio = panel.find_elements(By.NAME, "sort")
        self.assertTrue(radio[0].is_selected())

        # Descending checkbox isn't selected
        descending = panel.find_element(By.ID, "id_desc")
        self.assertFalse(descending.is_selected())

        # He sorts by modified
        radio[3].find_element(By.XPATH, "./following-sibling::span").click()
        self.sleep()

        # He sees first bundlename is the first
        cards = self.find_elems_by_class("cardiv")
        self.assertEqual(cards[0].get_attribute("data-name"), "Bundle-first")

        # He clicks descending
        descending.find_element(By.XPATH, "./following-sibling::span").click()
        self.sleep()

        # He sees abc bundlename is the first now
        cards = self.find_elems_by_class("cardiv")
        self.assertEqual(cards[0].get_attribute("data-name"), "Bundle-abc")

        panel = self.find_elem_by_id("id_panel")
        descending = panel.find_element(By.ID, "id_desc")
        radio = panel.find_elements(By.NAME, "sort")

        # He clicks descending
        descending.find_element(By.XPATH, "./following-sibling::span").click()
        self.sleep()

        # He sorts by modified
        radio[3].find_element(By.XPATH, "./following-sibling::span").click()
        self.sleep()

        # He sees a new bundlename is the first
        cards = self.find_elems_by_class("cardiv")
        self.assertEqual(cards[0].get_attribute("data-name"), "Bundle-first")

        panel = self.find_elem_by_id("id_panel")
        descending = panel.find_element(By.ID, "id_desc")
        radio = panel.find_elements(By.NAME, "sort")

        # He clicks descending
        descending.find_element(By.XPATH, "./following-sibling::span").click()
        self.sleep()

        # He sorts by modified
        radio[3].find_element(By.XPATH, "./following-sibling::span").click()
        self.sleep()

        # He sees default title is the last
        cards = self.find_elems_by_class("cardiv")
        self.assertEqual(cards[-1].get_attribute("data-name"), "Bundle-first")


class HomePageScriptsTest(FunctionalTest):
    """The home page's own script has to actually initialise.

    Sorting and filtering are bound by ``mainHome`` on document ready. When the
    base template stopped loading jQuery, that binding silently never happened
    and every sorting assertion failed with a plausible-looking wrong order
    rather than an error -- so this checks the environment directly, and says
    what it found when it is wrong.
    """

    def _js_state(self):
        return self.browser.execute_script(
            "var jq = (typeof window.jQuery === 'function');"
            "var filter = document.getElementById('id_filter');"
            "var bound = false;"
            "if (jq && filter) {"
            "  var ev = window.jQuery._data(filter, 'events');"
            "  bound = !!(ev && (ev.keyup || ev.change));"
            "}"
            "return {"
            "  jquery: jq,"
            "  scripts: Array.from(document.scripts)"
            "    .map(function (s) { return s.src.split('/').pop(); })"
            "    .filter(Boolean),"
            "  hasPanel: !!document.getElementById('id_panel'),"
            "  cards: document.querySelectorAll('.bundlenames > div').length,"
            "  filterBound: bound"
            "};"
        )

    def test_home_page_scripts_load_and_bind(self):
        self.create_cookie_and_go_to_bundlename_add_page(
            "scripts@example.com", permission=258_885_438_200
        )
        self.submit_bundlename_name("Bundle one", TEST_ADDRESS)
        self.browser.get(self.server_url + "/profile/add-bundle")
        self.submit_bundlename_name("Bundle two", f"{TEST_ADDRESS} {TEST_ADDRESS2}")
        self.browser.get(self.server_url + "/home/")

        state = self._js_state()
        why = f"\n  page state: {state}"
        self.assertTrue(state["jquery"], f"jQuery did not load{why}")
        # The template names the source (`js/home.js`); in production
        # ManifestStaticFilesStorage serves it under a content-hashed name, so
        # the assertion is on the stem rather than the exact filename.
        self.assertTrue(
            any(name.startswith("home.") for name in state["scripts"]),
            f"the page never requested its own script{why}",
        )
        self.assertTrue(state["hasPanel"], f"no sort/filter panel rendered{why}")
        self.assertGreater(
            state["cards"], 0, f".bundlenames has no direct div children{why}"
        )
        self.assertTrue(
            state["filterBound"],
            f"mainHome never bound its handlers -- sorting and filtering are "
            f"inert{why}",
        )

    def test_clicking_a_sort_option_reaches_the_handler(self):
        """Follow one click through every link in the chain.

        A wrong order tells you the outcome was wrong but not which step
        failed: the click may not have reached the radio, the radio may not
        have fired `change`, or the handler may not have been bound. This
        reports all three.

        The two names are deliberately added in the reverse of their
        alphabetical order. The page renders them sorted by name, so sorting by
        modified has to move something -- with names added in order, "nothing
        moved" would be the correct outcome and the test would prove nothing.
        """
        self.create_cookie_and_go_to_bundlename_add_page(
            "clicks@example.com", permission=258_885_438_200
        )
        self.submit_bundlename_name("Bundle zulu", TEST_ADDRESS)
        self.browser.get(self.server_url + "/profile/add-bundle")
        self.submit_bundlename_name("Bundle alpha", f"{TEST_ADDRESS} {TEST_ADDRESS2}")
        self.browser.get(self.server_url + "/home/")

        # Record whether the handler ever runs, without changing home.js.
        self.browser.execute_script(
            "window.__sortFired = 0;"
            "window.jQuery('input[name=sort]').on('change', function () {"
            "  window.__sortFired += 1;"
            "});"
        )
        before = self.browser.execute_script(
            "return Array.from(document.querySelectorAll('.bundlenames > div'))"
            "  .map(function (d) { return d.getAttribute('data-name'); });"
        )
        panel = self.find_elem_by_id("id_panel")
        modified = panel.find_elements(By.NAME, "sort")[3]
        modified.find_element(By.XPATH, "./following-sibling::span").click()
        self.sleep()

        after = self.browser.execute_script(
            "return {"
            "  checked: document.getElementById('id_modified').checked,"
            "  fired: window.__sortFired,"
            "  order: Array.from(document.querySelectorAll('.bundlenames > div'))"
            "    .map(function (d) { return d.getAttribute('data-name'); })"
            "};"
        )
        why = f"\n  before: {before}\n  after: {after}"
        self.assertTrue(after["checked"], f"the click never checked the radio{why}")
        self.assertGreater(after["fired"], 0, f"no change event was fired{why}")
        self.assertNotEqual(
            after["order"], before, f"the handler ran but nothing moved{why}"
        )
