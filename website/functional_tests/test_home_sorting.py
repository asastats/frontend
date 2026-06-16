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
        self.accept_cookie()

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
        self.accept_cookie()

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
