from selenium.webdriver.common.by import By

from .base import TESTING_ADDRESS, FunctionalTest


class ProfileAuthorizeWalletTest(FunctionalTest):
    def test_profile_authorize_page_offers_wallet_connect_and_escrow(self):
        # Wanda has signed up and set her Algorand address, but has not
        # authorized it yet, so she opens the authorization page
        self.create_cookie_and_go_to_authorize_page("wanda20@dwight.com")
        self.accept_cookie()

        # She is on the authorization page and sees the address being authorized
        self.assertIn("/profile/authorize/", self.browser.current_url)
        self.assertIn(TESTING_ADDRESS, self.browser.page_source)

        # The primary option is to connect a wallet
        wallet_connect = self.find_elem_by_id("wallet-connect")
        self.assertIn("Connect a wallet", wallet_connect.text)

        # Each supported wallet is offered as its own card with a Connect button
        pera_card = self.find_elem_by_id("wallet-pera")
        self.assertIn("Pera", pera_card.text)
        connect_button = self.find_elem_by_id("connect-button-pera")
        self.assertEqual("CONNECT", connect_button.text)

        # The set-active, disconnect and authorize controls start hidden, shown
        # by the bundle once a wallet connects
        for control in (
            "set-active-button-pera",
            "disconnect-button-pera",
            "auth-button-pera",
        ):
            element = self.find_elem_by_id(control)
            self.assertEqual("none", element.value_of_css_property("display"))

        # She also sees the manual-transaction fallback offered as a secondary,
        # collapsible option
        self.assertIn(
            "Authorize with a manual transaction instead", self.browser.page_source
        )

        # The fallback shows the Administration pool address and a button to
        # check the transaction once sent
        self.assertIn(
            "E7TR4BUASOGSHRRE2IBUHTHSNZGKU2DQDU5UF77L7VBITNVQGW5SCMS7OI",
            self.browser.page_source,
        )
        check_link = self.find_elem_by_id("id_check")
        self.assertIn("/profile/authorize/check/", check_link.get_attribute("href"))

    def test_profile_authorize_page_redirects_already_authorized_user(self):
        # Walter has already authorized his address (tier user), so the
        # authorization page is not available to him
        self.create_cookie_and_go_to_index_page_tier(
            "walter21@dwight.com", permission=100
        )
        with self.wait_for_page_load(timeout=5):
            self.browser.get(self.server_url + "/profile/authorize/")

        # He does not land on the authorization page
        self.assertNotIn("/profile/authorize/", self.browser.current_url)
