from django.contrib.auth import get_user_model
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By  # noqa: F401 (kept for parity/extension)

from .base import FunctionalTest

# Throwaway test account (holds no funds; the signed txn is never broadcast).
# The address MUST equal mnemonicToSecretKey(TEST_WALLET_MNEMONIC).addr so the
# nonce/verify address binding matches the profile address set below.
TEST_WALLET_ADDRESS = "GK4CNZ5G7T6642L44HELNKBWTG7TITPOZXVHFUHF7F7TTFGI4ZT3TIQPXQ"
TEST_WALLET_MNEMONIC = (
    "anchor kidney review slogan bar grit update patient envelope snake popular "
    "shoulder area require quarter craft essay turn uncle cry gauge gap scale "
    "abstract segment"
)


class ProfileAuthorizeWalletSigningTest(FunctionalTest):
    """End-to-end wallet authorization via the test-only mock wallet harness.

    Prerequisites for this test to run:
      * the bundle is built and served (``js/bundle.js``),
      * ``settings.WALLET_TEST_MODE`` is True for the functional-test settings,
        so the page loads the harness and exposes ``__installMockWallet``.
    The signature is genuine and verified by the unmodified MainNet-pinned
    backend; only the wallet extension is replaced.
    """

    def test_profile_authorize_wallet_sign_authorizes_and_redirects(self):
        # Mona has set her Algorand address and opens the authorization page
        self.create_cookie_and_go_to_authorize_page(
            "mona22@dwight.com", address=TEST_WALLET_ADDRESS
        )
        self.accept_cookie()

        # A mock wallet (controlling Mona's address) is installed in place of a
        # real browser extension. Wait until the test harness has attached its
        # global before calling it (guards against any load-order timing).
        WebDriverWait(self.browser, 10).until(
            lambda d: d.execute_script(
                "return typeof window.__installMockWallet === 'function'"
            )
        )
        installed_address = self.browser.execute_script(
            "return window.__installMockWallet(arguments[0]);", TEST_WALLET_MNEMONIC
        )
        self.assertEqual(TEST_WALLET_ADDRESS, installed_address)

        # She connects the wallet
        self.find_elem_by_id("connect-button-mock").click()
        self.sleep()

        # ... makes it active ...
        self.find_elem_by_id("set-active-button-mock").click()
        self.sleep()

        # ... and authorizes the address; the backend verifies the real
        # signature and redirects her to her profile
        with self.wait_for_page_load(timeout=10):
            self.find_elem_by_id("auth-button-mock").click()
        self.assertIn("/profile/", self.browser.current_url)
        self.assertNotIn("/authorize", self.browser.current_url)

        # The address is now authorized on her profile, recorded as a wallet auth
        user = get_user_model().objects.get(username="mona22@dwight.com")
        user.profile.refresh_from_db()
        self.assertTrue(user.profile.authorized)
        self.assertEqual("algorand_wallet", user.profile.auth_method)
