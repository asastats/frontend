from selenium.webdriver.common.by import By

from .base import FunctionalTest


class CustomAuthTest(FunctionalTest):
    def assertLabel(self, element, expected):
        """Assert an element's visible text, ignoring case.

        Materialize upper-cased buttons and links in CSS, so these assertions
        used to spell the expectation in capitals. DaisyUI does not, which
        makes the rendered casing a design decision rather than something the
        content depends on -- so they now compare the words.
        """
        self.assertIn(expected.strip().lower(), element.text.strip().lower())

    def test_custom_auth_page(self):
        # Don goes to signup page
        with self.wait_for_page_load(timeout=5):
            self.browser.get(self.server_url + "/accounts/signup/")


        # He sees sign up header
        header = self.find_elem_by_tag("h3")
        self.assertIn("Sign up", header.text)

        # He sees input field for login with hint text in it
        elem = self.find_elem_by_id("id_email")
        self.assertIn("Email address", elem.get_attribute("placeholder"))

        # Also input field for password with hint text in it
        elem = self.browser.find_element(By.XPATH, '//label[@for="id_password1"]')
        self.assertIn("Password", elem.text)

        # And another input field for password
        elem = self.browser.find_element(By.XPATH, '//label[@for="id_password2"]')
        self.assertIn("Password (again)", elem.text)

        # There are login by social media account buttons too
        social = self.find_elem_by_id("id_discord")
        self.assertIn("/accounts/discord/login/", social.get_attribute("href"))
        social = self.find_elem_by_id("id_twitter")
        self.assertIn("/accounts/twitter_oauth2/login/", social.get_attribute("href"))
        social = self.find_elem_by_id("id_reddit")
        self.assertIn("/accounts/reddit/login/", social.get_attribute("href"))
        social = self.find_elem_by_id("id_github")
        self.assertIn("/accounts/github/login/", social.get_attribute("href"))
        social = self.find_elem_by_id("id_google")
        self.assertIn("/accounts/google/login/", social.get_attribute("href"))

        buttons = self.browser.find_elements(By.CLASS_NAME, "primaryAction")
        self.assertLabel(buttons[0], "Sign up")

        # There's the button asking if he maybe already has an account
        links = self.browser.find_elements(By.XPATH, '//a[@href="/accounts/login/"]')
        self.assertLabel(links[1], "Already have an account?")

        # He clicks that button and finds himself in login page
        with self.wait_for_page_load(timeout=5):
            links[1].click()

        # He sees sign up header
        header = self.find_elem_by_tag("h3")
        self.assertIn("Login", header.text)

        # He sees input field for login with hint text in it
        elem = self.find_elem_by_id("id_login")
        self.assertIn("Username or email", elem.get_attribute("placeholder"))

        # Also input field for password with hint text in it
        elem = self.browser.find_element(By.XPATH, '//label[@for="id_password"]')
        self.assertIn("Password", elem.text)

        # There are login by social media account buttons too
        text = "Sign in with Discord"
        social = self.browser.find_element(By.LINK_TEXT, text)
        self.assertIn("/accounts/discord/login/", social.get_attribute("href"))
        text = "Sign in with X"
        social = self.browser.find_element(By.LINK_TEXT, text)
        self.assertIn("/accounts/twitter_oauth2/login/", social.get_attribute("href"))
        text = "Sign in with Reddit"
        social = self.browser.find_element(By.LINK_TEXT, text)
        self.assertIn("/accounts/reddit/login/", social.get_attribute("href"))
        text = "Sign in with GitHub"
        social = self.browser.find_element(By.LINK_TEXT, text)
        self.assertIn("/accounts/github/login/", social.get_attribute("href"))
        text = "Sign in with Google"
        social = self.browser.find_element(By.LINK_TEXT, text)
        self.assertIn("/accounts/google/login/", social.get_attribute("href"))

        # There's the button asking if he maybe don't have an account
        links = self.browser.find_elements(By.XPATH, '//a[@href="/accounts/signup/"]')
        self.assertLabel(links[1], "Don't have an account?")

        # Also the button asking if he maybe forgot his password
        links = self.browser.find_elements(
            By.XPATH, '//a[@href="/accounts/password/reset/"]'
        )
        self.assertIn("Forgot your password?", links[0].text)

        # # There's help button
        # elem = self.find_elem_by_id('id_help_auth')
        # self.assertLabel(elem, "Help")

        # There's large call to action button
        buttons = self.browser.find_elements(By.CLASS_NAME, "primaryAction")
        self.assertLabel(buttons[0], "Log in")

    def _click_modal_tab(self, panel_id):
        """Switch the login modal to the tab whose panel is ``panel_id``."""
        self.browser.find_element(By.XPATH, '//a[@href="#{}"]'.format(panel_id)).click()
        self.sleep()

    def _assert_social_links(self):
        """Assert the five provider links are present and correctly targeted."""
        for text, href in (
            ("Sign in with Discord", "/accounts/discord/login/"),
            ("Sign in with X", "/accounts/twitter_oauth2/login/"),
            ("Sign in with Reddit", "/accounts/reddit/login/"),
            ("Sign in with GitHub", "/accounts/github/login/"),
            ("Sign in with Google", "/accounts/google/login/"),
        ):
            social = self.browser.find_element(By.LINK_TEXT, text)
            self.assertIn(href, social.get_attribute("href"))

    def test_modal_custom_auth_page(self):
        # Dan goes to index page
        with self.wait_for_page_load(timeout=5):
            self.browser.get(self.server_url)


        # He sees login link and clicks it
        login = self.browser.find_element(By.XPATH, '//a[@href="#modalLogin"]')
        login.click()
        self.sleep()

        # He sees the log in header
        #
        # Found through the dialog's own id, which is what the link he just
        # clicked points at. It used to be `.modal-content`, a class with no
        # rule in any stylesheet and no script that read it -- it existed only
        # for this line, so the markup was carrying a hook for its own test.
        container = self.find_elem_by_id("modalLogin")
        header = container.find_element(By.TAG_NAME, "h3")
        self.assertIn("Log in", header.text)

        # The "Log in" tab is the default: its input fields are visible
        elem = self.find_elem_by_id("id_login_modal")
        self.assertIn("Username or email", elem.get_attribute("placeholder"))

        # Also input field for password with hint text in it
        elem = self.find_elem_by_id("id_password_modal")
        self.assertIn("Password", elem.get_attribute("placeholder"))

        # # TODO uncomment this if we solve checkbox bug
        # # And password remember field
        # elem = self.find_elem_by_id('id_remember_modal')
        # self.assertEqual('checkbox', elem.get_attribute('type'))

        # And the call to action button lives on this default tab
        elem = self.find_elem_by_id("id_cta_modal")
        self.assertLabel(elem, "Log in")

        # He switches to the Wallet tab and sees the Pera and Defly wallets
        self._click_modal_tab("modal-tab-wallet")
        pera = self.find_elem_by_id("wallet-pera")
        self.assertTrue(pera.is_displayed())
        self.assertIn("PERA", pera.text.upper())
        defly = self.find_elem_by_id("wallet-defly")
        self.assertTrue(defly.is_displayed())
        self.assertIn("DEFLY", defly.text.upper())

        # He returns to normal testing: the Social tab lists the providers
        self._click_modal_tab("modal-tab-social")
        self._assert_social_links()

        # There's the button asking if he maybe don't have an account
        links = self.browser.find_elements(By.XPATH, '//a[@href="/accounts/signup/"]')
        self.assertLabel(links[0], "Don't have an account?")

        # Also the button asking if he maybe forgot his password
        links = self.browser.find_elements(
            By.XPATH, '//a[@href="/accounts/password/reset/"]'
        )
        self.assertLabel(links[0], "Forgot Password?")

        # There's cancel button
        elem = self.find_elem_by_id("id_cancel")
        self.assertLabel(elem, "Cancel")


class WalletHandoffTest(FunctionalTest):
    """The login dialog steps aside for a wallet picker, and comes back.

    ``showModal()`` puts the dialog in the browser's top layer, above every
    element in the normal layer whatever its z-index. Wallet SDKs append their
    picker to ``<body>`` as ordinary DOM, so from inside the dialog it was
    painted underneath and could not be reached. The dialog therefore closes as
    the picker opens and reopens when the reader is wanted back.

    **Reopening had one cue and needed two.** Watching the picker leave assumes
    the SDK appends its container after the handoff was armed. That holds for a
    first connect and fails for a reconnect -- a reader whose wallet session was
    restored from a previous visit, who disconnects and connects again, meets an
    SDK whose container is already on the body. Nothing is recorded as injected,
    nothing is seen to leave, and the dialog stayed shut: they had to click Log
    in a second time to reach Sign in and sign the 0 ALGO message.

    So the connection is watched as well, through the controls the wallet card
    reveals. That is what these drive, in a real browser against the real
    snippet. The jest suite covers the same logic against a hand-built fixture,
    which cannot tell whether ``wallet_signing.html`` still renders the ids the
    selector names -- and those ids are the whole contract.
    """

    def _open_wallet_tab(self):
        """Open the login dialog on the wallet tab, as a reader does."""
        self.browser.get(self.server_url)
        self.browser.find_element(By.XPATH, '//a[@href="#modalLogin"]').click()
        self.browser.find_element(
            By.XPATH, '//a[@href="#modal-tab-wallet"]'
        ).click()
        return self.wait_until(
            lambda: self.find_elem_by_id("modalLogin").get_attribute("open")
            is not None
        )

    def _warm_the_sdk(self):
        """Put a wallet SDK's container on the body before the handoff arms.

        This is the state a reconnect starts from, and the reason the picker cue
        alone was not enough: the container is already there to be snapshotted
        as "the page", so its later reuse is invisible.
        """
        self.browser.execute_script(
            "var el = document.createElement('div');"
            "el.id = 'pera-wallet-modal';"
            "document.body.appendChild(el);"
        )

    def _connection_lands(self):
        """Reveal Sign in, which is what `frontend/wallet` does on connect.

        The wallet package itself needs a wallet extension and a real signature,
        so what it *does to the page* is what stands in for it -- one property
        on one button, which is exactly what the handoff reads.
        """
        self.browser.execute_script(
            "document.getElementById('auth-button-pera').style.display = 'block';"
        )

    def _dialog_open(self):
        return (
            self.find_elem_by_id("modalLogin").get_attribute("open") is not None
        )

    def test_the_dialog_steps_aside_when_a_connect_starts(self):
        self._open_wallet_tab()

        self.browser.find_element(By.ID, "connect-button-pera").click()

        self.wait_until(lambda: not self._dialog_open(), timeout=10)

    def test_it_comes_back_when_the_connection_lands(self):
        """The bug, in the state that produced it: a warm SDK.

        Nothing is appended to the body here and nothing is removed from it, so
        the picker cue has nothing to say. The reader still has to be brought
        back, because Sign in is inside the dialog they cannot see.
        """
        self._open_wallet_tab()
        self._warm_the_sdk()
        self.browser.find_element(By.ID, "connect-button-pera").click()
        self.wait_until(lambda: not self._dialog_open(), timeout=10)

        self._connection_lands()

        self.wait_until(self._dialog_open, timeout=10)
        # ...and on the wallet tab, where Sign in is.
        self.assertTrue(self.find_elem_by_id("modal-tab-wallet").is_displayed())
        self.assertTrue(self.find_elem_by_id("auth-button-pera").is_displayed())

    def test_it_stays_away_while_nothing_has_connected(self):
        """The cue is a connection, not any activity on the card at all.

        Without this the dialog would come back over the picker on the first
        thing the SDK touched, which is the failure the handoff exists to
        prevent.
        """
        self._open_wallet_tab()
        self._warm_the_sdk()
        self.browser.find_element(By.ID, "connect-button-pera").click()
        self.wait_until(lambda: not self._dialog_open(), timeout=10)

        self.browser.execute_script(
            "document.getElementById('account-select-pera').style.display = 'block';"
        )
        self.sleep()

        self.assertFalse(self._dialog_open())
