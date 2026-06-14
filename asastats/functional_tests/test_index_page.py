from .base import TESTING_ADDRESS, FunctionalTest


class IndexPageTest(FunctionalTest):
    def test_index_page_has_whenmoon_button_that_leads_to_address_page(self):
        self.browser.get(self.server_url)

        self.assertIn("ASA Stats", self.browser.title)

        address = self.find_elem_by_id("id_address")
        address.clear()
        address.send_keys(TESTING_ADDRESS)

        button = self.find_elem_by_id("whenmoon")
        self.assertIn("WHEN MOON", button.text)

        with self.wait_for_page_load(timeout=2):
            self.find_elem_by_id("whenmoon").click()
        self.assertIn(TESTING_ADDRESS, self.browser.current_url)
