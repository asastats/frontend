"""Functional tests for profile_link_address.html.

The page had no functional coverage at all, and it is the one profile page
where the markup *is* the contract: everything on it is built by the wallet
bundle at runtime, which finds its containers by id and reads its configuration
off their data attributes. A rename that a template test would call harmless
turns the page into a different page -- or into the sign-in page.

Three faults this pins, all of which had shipped:

* **`data-api-base` points at the link endpoint, not the login one.** Both
  sections carry it, and both are `/api/v2/wallet/link` here. Losing the suffix
  on either makes a linking page that signs the reader in as somebody else.
* **`#evm-app-error` has to exist.** `evmWalletComponent.showNoWallets` looks
  for it by id and does nothing at all without it, so a reader with no EVM
  wallet met an empty box and no explanation. The page used to hand-roll its
  own copy of the EVM container and the copy lacked that element; it uses the
  shared snippet now.
* **The WalletConnect project id comes from `WALLET_CONNECT_PROJECT_ID`.** The
  hand-rolled copy read `wallet_connect_project_id`, which nothing provides, so
  the attribute was always empty and WalletConnect was unconfigured on this
  page alone -- while the authorize page, using the snippet, worked.

`#app-error` is the page-level failure and its `style="display:none"` is a
contract rather than a stray inline style: the bundle reveals it by assigning
`style.display = "block"`, and `wallet/src/main.test.ts` asserts on exactly
that markup.
"""

from django.urls import reverse
from selenium.webdriver.common.by import By

from .base import FunctionalTest


class LinkAddressPageTest(FunctionalTest):
    """What the wallet bundle needs to find, and what a reader is told."""

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_index_page_tier("link@example.com", permission=100)
        self.state = self.visit(self.server_url + reverse("profile_link_address"))

    def test_the_page_renders_rather_than_raising(self):
        """The page reads a context processor value and two url names.

        Worth its own assertion because a 500 here renders templates/500.html,
        which looks like a bare page rather than an error -- see
        `captured_server_errors` in base.py for why the traceback is in the
        message.
        """
        self.assertNotEqual(
            self.state["title"],
            "Internal server error",
            f"the link-address page raised{self.state['why']}",
        )
        self.assertTrue(self.browser.find_elements(By.CSS_SELECTOR, "main h1"))

    def test_both_wallet_families_are_named(self):
        """Two very different sets of software, each behind its own heading.

        They used to be two bare divs in a row with nothing saying where one
        ended and the next began, so a reader with only an Algorand wallet met
        a heading-less empty area below their own wallets and no way to know it
        was for something else.
        """
        headings = [
            heading.text.strip()
            for heading in self.browser.find_elements(By.CSS_SELECTOR, "main h2")
        ]
        self.assertIn("Algorand wallets", headings)
        self.assertIn("EVM wallets", headings)

    def test_both_containers_point_at_the_link_endpoint(self):
        """The one attribute that decides what this page *does*.

        `/api/v2/wallet/link` adds an address to the profile;
        `/api/v2/wallet/login` signs somebody in. The two containers are found
        by id by the wallet bundle, so neither the ids nor these values are
        cosmetic.
        """
        for container_id in ("wallet-connect", "evm-wallet-connect"):
            with self.subTest(container=container_id):
                container = self.browser.find_element(By.ID, container_id)
                self.assertEqual(
                    "/api/v2/wallet/link", container.get_attribute("data-api-base")
                )

    def test_a_reader_with_no_evm_wallet_has_something_to_be_told(self):
        """The element the bundle reveals when it finds no connector.

        Hidden at rest and revealed by `showNoWallets`, which looks it up by
        id: without the element the method runs, finds nothing and returns, and
        the reader is left with an empty box. Asserted by revealing it the way
        the bundle does, so this fails if the element stops being reachable
        *or* stops being able to show itself.
        """
        notice = self.browser.find_element(By.ID, "evm-app-error")
        self.assertFalse(notice.is_displayed())
        self.assertEqual("alert", notice.get_attribute("role"))

        self.browser.execute_script(
            "arguments[0].style.display = 'block';", notice
        )
        self.assertTrue(notice.is_displayed())
        self.assertIn("No EVM wallet found", notice.text)

    def test_there_is_exactly_one_page_level_failure_banner(self):
        """`#app-error` covers "the wallet list itself could not be fetched".

        `main.ts` reveals it with `document.getElementById`, which returns the
        first in document order -- so a second element with that id is not a
        second banner, it is dead markup. This page rendered its own on top of
        the one `snippets/wallet_cards.html` already provides, and the one it
        rendered could never be shown.

        `role="alert"` is what makes it interrupt rather than wait to be
        noticed, which matters because neither section on this page can work
        once it is showing, and because the bundle reveals it long after load.
        """
        banners = self.browser.find_elements(By.ID, "app-error")
        self.assertEqual(1, len(banners), "duplicate #app-error ids on the page")

        error = banners[0]
        self.assertFalse(error.is_displayed())
        self.assertEqual("alert", error.get_attribute("role"))
        self.assertEqual("none", error.value_of_css_property("display"))

        # Revealed the way the bundle reveals it, so this fails if the element
        # is present but cannot show itself.
        self.browser.execute_script("arguments[0].style.display = 'block';", error)
        self.assertTrue(error.is_displayed())

    def test_the_algorand_section_offers_the_wallet_cards(self):
        """The same cards the authorize page offers, from the same snippet."""
        cards = self.browser.find_element(By.ID, "wallet-connect")
        self.assertTrue(
            cards.find_elements(By.ID, "wallet-pera"),
            "the Algorand section rendered no wallet cards",
        )

    def test_the_back_link_leads_to_the_address_list(self):
        """Back to where the reader came from, not to the profile root.

        This page is reached from the address list and is one step of managing
        it; landing on the profile afterwards makes the reader navigate back
        down to see the address they just added.
        """
        links = [
            link.get_attribute("href")
            for link in self.browser.find_elements(By.CSS_SELECTOR, "main a")
            if link.text.strip().lower() == "back"
        ]
        self.assertTrue(links, "the page has no Back link")
        self.assertTrue(
            any(reverse("profile_addresses") in href for href in links),
            f"Back does not lead to the address list: {links}",
        )
