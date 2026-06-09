from selenium.webdriver.common.by import By

from utils.tests.fixtures import TEST_ADDRESS, TEST_ADDRESS2, TEST_ADDRESS3

from .base import FunctionalTest


class HomeFilteringTest(FunctionalTest):
    def _visible_cards(self):
        return [
            card for card in self.find_elems_by_class("cardiv") if card.is_displayed()
        ]

    def test_home_bundlename_filtering_bundlenames(self):
        # Johnny signs up
        self.create_cookie_and_go_to_bundlename_add_page(
            "johnny_pro@example.com", permission=258_885_438_200
        )
        self.accept_cookie()

        # He adds a bundlename
        bundlename1 = "My first"
        self.submit_bundlename_name(bundlename1, TEST_ADDRESS)
        self.browser.get(self.server_url + "/home/")
        self.sleep()
        # He sees no panel
        panel = self.browser.find_elements(By.ID, "id_panel")
        self.assertEqual(len(panel), 0)

        # He adds more bundlenames
        self.browser.get(self.server_url + "/profile/add-bundle")
        self.sleep()
        bundlename2 = "My abc"
        self.submit_bundlename_name(bundlename2, f"{TEST_ADDRESS} {TEST_ADDRESS2}")
        self.sleep()
        self.browser.get(self.server_url + "/profile/add-bundle")
        self.sleep()
        bundlename3 = "Abc something"
        self.submit_bundlename_name(bundlename3, f"{TEST_ADDRESS} {TEST_ADDRESS3}")
        self.sleep()
        self.browser.get(self.server_url + "/home/")
        self.sleep()

        # He sees panel now
        panel = self.find_elem_by_id("id_panel")
        descending = panel.find_element(By.ID, "id_desc")
        radio = panel.find_elements(By.NAME, "sort")

        # There are three visible bundlenames
        cards = self._visible_cards()
        self.assertEqual(len(cards), 3)

        # He enters characters in filtering input box
        filtering = self.find_elem_by_id("id_filter")
        filtering.clear()
        filtering.send_keys("my")
        self.sleep()

        # There are two visible bundlenames now
        cards = self._visible_cards()
        self.assertEqual(len(cards), 2)

        # He sees first bundlename is the abc
        self.assertEqual(cards[0].get_attribute("data-name"), "My-abc")

        # And the second is bundlename first
        self.assertEqual(cards[1].get_attribute("data-name"), "My-first")

        # He sorts by created
        radio[2].find_element(By.XPATH, "./following-sibling::span").click()
        self.sleep()

        # He sees bundlename first bundlename is now the first
        cards = self._visible_cards()
        self.assertEqual(cards[0].get_attribute("data-name"), "My-first")

        # And there are still two bundlenames
        self.assertEqual(len(cards), 2)

        # He clicks descending
        descending.find_element(By.XPATH, "./following-sibling::span").click()
        self.sleep()

        # He sees abc bundlename is the first now
        cards = self._visible_cards()
        self.assertEqual(cards[0].get_attribute("data-name"), "My-abc")

        # He removes characters from filtering input box
        filtering = self.find_elem_by_id("id_filter")
        filtering.clear()
        self.sleep()

        # There are three bundlenames now
        cards = self._visible_cards()
        self.assertEqual(len(cards), 3)

        # He enters characters in filtering input box
        filtering = self.find_elem_by_id("id_filter")
        filtering.clear()
        filtering.send_keys("ab")
        self.sleep()

        # There are two visible bundlenames now
        cards = self._visible_cards()
        self.assertEqual(len(cards), 2)

        # He sees first bundlename is the something
        self.assertEqual(cards[0].get_attribute("data-name"), "Abc-something")

        # And the second is bundlename abc
        self.assertEqual(cards[1].get_attribute("data-name"), "My-abc")

        # He removes characters from filtering input box
        filtering = self.find_elem_by_id("id_filter")
        filtering.clear()
        self.sleep()

        # There are three bundlenames now
        cards = self._visible_cards()
        self.assertEqual(len(cards), 3)

        # He enters characters in filtering input box
        filtering = self.find_elem_by_id("id_filter")
        filtering.clear()
        filtering.send_keys(TEST_ADDRESS3[:5])
        self.sleep()

        # There are one bundlename now
        cards = self._visible_cards()
        self.assertEqual(len(cards), 1)

        # It is Abc something
        self.assertEqual(cards[0].get_attribute("data-name"), "Abc-something")
