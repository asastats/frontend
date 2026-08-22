from selenium.webdriver.common.by import By

from .base import TESTING_ADDRESS, FunctionalTest


class ProfileAuthorizeWalletTest(FunctionalTest):
    def test_profile_authorize_page_offers_wallet_connect_and_escrow(self):
        # Wanda has signed up and set her Algorand address, but has not
        # authorized it yet, so she opens the authorization page
        self.create_cookie_and_go_to_authorize_page("wanda20@dwight.com")

        # She is on the authorization page and sees the address being authorized
        self.assertIn("/profile/authorize/", self.browser.current_url)
        self.assertIn(TESTING_ADDRESS, self.browser.page_source)

        # The primary option is to connect a wallet
        wallet_connect = self.find_elem_by_id("wallet-connect")
        self.assertIn("Prove control of the address", wallet_connect.text)

        # Each supported wallet is offered as its own card with a Connect button
        pera_card = self.find_elem_by_id("wallet-pera")
        self.assertIn("Pera", pera_card.text)
        connect_button = self.find_elem_by_id("connect-button-pera")
        # Materialize upper-cased button and link text in CSS; DaisyUI does
        # not, so the rendered casing is a design decision now rather than
        # something the content depends on.
        self.assertEqual("connect", connect_button.text.strip().lower())

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


class ProfileAuthorizeRebuildTest(FunctionalTest):
    """What the 2026-08-22 rebuild of this page has to keep true.

    The page was rebuilt from one that used `<blockquote>` for addresses,
    `<br><br>` for spacing, a Materialize collapsible nothing initialises any
    more, and a messages block carrying four colour classes at once
    (`badge-outline bg-neutral text-neutral-content text-base-content/60`), so
    which one won depended on source order. None of that fails a template test.
    """

    #: Replaces the real clipboard: headless Chrome will not write to it
    #: without a permission grant, and `site.js` skips the copy entirely when
    #: `navigator.clipboard` is absent -- so a test that let it be absent would
    #: pass against a control bound to nothing.
    CLIPBOARD_STUB = """
    window.__copied = [];
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText: function (text) {
          window.__copied.push(text);
          return Promise.resolve();
        }
      }
    });
    """

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_authorize_page("rebuild@dwight.com")

    def test_the_addresses_are_monospace_and_copyable(self):
        """An Algorand address in a proportional face cannot be checked by eye.

        They are `<code>` now rather than `<blockquote>` -- nothing here is
        being quoted -- and each has a copy control, because these exist to be
        copied exactly. `copyToClipboard` reads `$(this).prev()`, so a wrapper
        between the two would leave the control bound, looking right, and
        copying the wrong thing.
        """
        self.browser.execute_script(self.CLIPBOARD_STUB)

        self.assertFalse(
            self.browser.find_elements(By.TAG_NAME, "blockquote"),
            "the page still quotes an address it is asking the reader to copy",
        )
        # The manual route is a closed <details>; its controls have no geometry
        # until it is open, and a click on a hidden button does not land.
        self.browser.execute_script(
            "document.querySelectorAll('details')"
            ".forEach(function (d) { d.open = true; });"
        )

        controls = self.browser.find_elements(By.CSS_SELECTOR, "main button.copy")
        self.assertGreaterEqual(len(controls), 3, "an address lost its copy control")

        expected = []
        for control in controls:
            expected.append(
                self.browser.execute_script(
                    "return arguments[0].previousElementSibling.textContent.trim();",
                    control,
                )
            )
            control.click()

        copied = self.browser.execute_script("return window.__copied;")
        self.assertEqual(expected, copied, "a copy control copied nothing")
        # The reader's own address and the pool address are among them, so this
        # is not three controls all copying the same thing.
        self.assertIn(TESTING_ADDRESS, copied)
        self.assertIn(
            "E7TR4BUASOGSHRRE2IBUHTHSNZGKU2DQDU5UF77L7VBITNVQGW5SCMS7OI", copied
        )

    def test_the_manual_route_is_announced_and_opens_without_javascript(self):
        """A native `<details>`, closed by default and labelled.

        It was a Materialize collapsible and nothing on this page initialises
        one any more, so it opened for nobody. Closed by default because
        connecting is the route most readers want -- but announced by a heading
        rather than sitting unlabelled at the foot of the page.
        """
        manual = self.browser.find_element(By.CSS_SELECTOR, "main details")
        self.assertIsNone(manual.get_attribute("open"))

        summary = manual.find_element(By.TAG_NAME, "summary")
        self.assertIn("manual transaction", summary.text.lower())

        check = self.browser.find_element(By.ID, "id_check")
        self.assertFalse(check.is_displayed(), "the fallback's controls start visible")

        summary.click()

        self.wait_until(lambda: check.is_displayed())

    def test_a_message_is_announced_rather_than_left_to_be_noticed(self):
        """The messages block carried four colour classes and no role.

        A message that appears after load and carries no role is announced to
        nobody. Django's messages are hard to provoke from a browser session,
        so this asserts on the shape the template gives them: whichever branch
        renders, it is an alert carrying a live-region role.
        """
        source = self.browser.page_source
        self.assertNotIn("badge-outline bg-neutral", source)

        # The template's two branches, verified against the rendered stylesheet
        # rather than trusted: `alert-error` must resolve to something, or the
        # error branch is a plain box.
        painted = self.browser.execute_script(
            "var probe = document.createElement('div');"
            "probe.className = 'alert alert-error';"
            "document.body.appendChild(probe);"
            "var colour = getComputedStyle(probe).backgroundColor;"
            "probe.remove();"
            "return colour;"
        )
        self.assertNotIn(painted, ("", "rgba(0, 0, 0, 0)", "transparent"))
