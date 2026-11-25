"""Functional tests for the DAO vote panel on a session page."""

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from selenium.webdriver.common.by import By

from daovoting.tests import fakes
from walletauth.models import LinkedAddress

from .base import COOKIE_SEED_URL, FunctionalTest

#: Records every request and answers like a wallet would; `window.__votes` holds them.
STUB_VOTE_API = """
window.__votes = [];
var fail = arguments[0];
window.asastatsVote = {
  accounts: function () { return []; },
  connect: function () { return Promise.resolve([]); },
  castVote: function (request) {
    window.__votes.push(request);
    return fail ? Promise.reject(new Error(fail)) : Promise.resolve('STUBTXID');
  }
};
"""


@override_settings(DAO_PROVIDER="daovoting.tests.fakes.FakeProvider")
class DaoVotePanelTest(FunctionalTest):
    """A governor with a linked seat votes from the session page."""

    def _sign_in_with_seat(self, email="governor@example.com"):
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=100
        )
        user = get_user_model().objects.get(username=email)
        LinkedAddress.objects.create(
            profile=user.profile,
            address=fakes.SEAT_A,
            canonical_address=fakes.SEAT_A,
            chain="algorand",
            auth_method="algorand_wallet",
        )
        self.browser.get(self.server_url + COOKIE_SEED_URL)
        self.browser.add_cookie(session_cookie)

    def _open_session(self, session_id=2):
        self.browser.get(self.server_url + reverse("dao_session", args=[session_id]))
        return self.find_elem_by_id("id-dao-vote-panel")

    def _card(self):
        return self.find_elem_by_css(f'[data-vote-seat="{fakes.SEAT_A}"]')

    def _stub_and_vote(self, option, fail=""):
        self.wait_until(
            lambda: self.browser.execute_script(
                "var p = document.getElementById('id-dao-vote-panel');"
                "return p && p.dataset.voteBound === 'true';"
            )
        )
        self.browser.execute_script(STUB_VOTE_API, fail)
        self._card().find_element(
            By.CSS_SELECTOR, f'[data-vote-option="{option}"]'
        ).click()

    def _status(self):
        return self._card().find_element(By.CSS_SELECTOR, "[data-vote-status]").text

    def test_a_governor_sees_their_seat_with_its_snapshot_venues(self):
        self._sign_in_with_seat()
        panel = self._open_session()
        self.assertEqual(panel.get_attribute("data-permission-app-id"), "750094865")
        self.assertEqual(
            panel.get_attribute("data-vote-method"), "vote(uint64,uint64)void"
        )
        card = self._card()
        self.assertEqual(
            card.find_element(By.CSS_SELECTOR, "[data-vote-eligible]").text, "50"
        )
        self.assertEqual(
            card.find_element(By.CSS_SELECTOR, "[data-vote-weight]").text, "50"
        )
        self.assertEqual(
            card.find_element(By.CSS_SELECTOR, "[data-vote-current]").text, "Option 0"
        )
        card.find_element(By.TAG_NAME, "summary").click()
        venues = card.find_element(By.CSS_SELECTOR, "[data-vote-venues]").text
        self.assertIn("Wallet", venues)
        self.assertIn("gat 1047879402", venues)
        self.assertEqual(
            len(card.find_elements(By.CSS_SELECTOR, "button[data-vote-option]")), 2
        )

    def test_the_wallet_buttons_come_from_the_supported_wallets(self):
        self._sign_in_with_seat()
        panel = self._open_session()
        buttons = self.wait_until(
            lambda: panel.find_elements(
                By.CSS_SELECTOR, "[data-vote-wallets] button[data-vote-connect]"
            )
        )
        self.assertTrue(all(b.text.startswith("Connect ") for b in buttons))

    def test_voting_signs_the_request_and_reports_the_transaction(self):
        self._sign_in_with_seat()
        self._open_session()
        self._stub_and_vote(1)
        self.wait_until(lambda: "STUBTXID" in self._status())
        self.assertIn("Vote for Option 1 confirmed", self._status())
        card = self._card()
        self.assertEqual(
            card.find_element(By.CSS_SELECTOR, "[data-vote-current]").text, "Option 1"
        )
        self.assertEqual(
            [
                b.text
                for b in card.find_elements(By.CSS_SELECTOR, "button[data-vote-option]")
            ],
            ["Change to Option 0", "Option 1 (your vote)"],
        )
        request = self.browser.execute_script("return window.__votes[0];")
        self.assertEqual(
            request,
            {
                "seat": fakes.SEAT_A,
                "appId": 775947805,
                "permissionAppId": 750094865,
                "sessionId": 2,
                "option": 1,
                "method": "vote(uint64,uint64)void",
            },
        )

    def test_a_refused_vote_shows_the_reason(self):
        self._sign_in_with_seat()
        self._open_session()
        self._stub_and_vote(0, fail="Voting has ended")
        self.wait_until(lambda: self._status() == "Voting has ended")
        self.assertTrue(
            self._card()
            .find_element(By.CSS_SELECTOR, '[data-vote-option="0"]')
            .is_enabled()
        )

    def test_a_closed_session_shows_the_seat_without_buttons(self):
        self._sign_in_with_seat()
        self._open_session(1)
        self.assertEqual(
            self._card().find_elements(By.CSS_SELECTOR, "button[data-vote-option]"), []
        )

    def test_a_visitor_is_asked_to_sign_in(self):
        self.browser.get(self.server_url + reverse("dao_session", args=[2]))
        self.assertTrue(self.find_elem_by_id("id-dao-sign-in").is_displayed())
        self.assertEqual(self.browser.find_elements(By.ID, "id-dao-vote-panel"), [])
