"""Functional tests for the read-only DAO voting pages."""

from django.test import override_settings
from django.urls import reverse
from selenium.webdriver.common.by import By

from daovoting.tests import fakes

from .base import FunctionalTest


@override_settings(DAO_PROVIDER="daovoting.tests.fakes.FakeProvider")
class DaoPagesTest(FunctionalTest):
    """A reader follows the sessions, one session and the governors."""

    def test_the_index_lists_every_session_with_its_phase(self):
        self.browser.get(self.server_url + reverse("dao_index"))
        self.assertEqual(self.browser.find_element(By.TAG_NAME, "h1").text, "DAO voting")
        cards = self.browser.find_elements(By.CSS_SELECTOR, "section[data-session]")
        self.assertEqual(
            [
                (card.get_attribute("data-session"), card.get_attribute("data-phase"))
                for card in cards
            ],
            [("4", "weighing"), ("3", "upcoming"), ("2", "voting"), ("1", "passed")],
        )

    def test_a_session_card_leads_to_its_page(self):
        self.browser.get(self.server_url + reverse("dao_index"))
        self.find_elem_by_link_text("Session 2").click()
        self.wait_for_page_load()
        self.assertTrue(
            self.browser.current_url.endswith(reverse("dao_session", args=[2]))
        )
        self.assertEqual(self.browser.find_element(By.TAG_NAME, "h1").text, "Session 2")

    def test_the_session_page_checks_the_proposal_and_shows_weights_so_far(self):
        self.browser.get(self.server_url + reverse("dao_session", args=[2]))
        check = self.browser.find_element(By.ID, "id-proposal-check")
        self.assertEqual(check.get_attribute("data-check"), "match")
        self.assertEqual(
            self.browser.find_element(By.ID, "id-final-check").get_attribute(
                "data-check"
            ),
            "unset",
        )
        self.assertIn("67100000", self.browser.find_element(By.ID, "id-dao-sofar").text)
        self.assertTrue(self.browser.find_element(By.ID, "id-dao-provisional"))
        self.assertIn("Raise the fee.", self.browser.page_source)

    def test_a_passed_session_checks_its_final_file(self):
        self.browser.get(self.server_url + reverse("dao_session", args=[1]))
        check = self.browser.find_element(By.ID, "id-final-check")
        self.assertEqual(check.get_attribute("data-check"), "match")

    def test_the_session_page_lists_every_ballot(self):
        self.browser.get(self.server_url + reverse("dao_session", args=[2]))
        rows = self.browser.find_elements(
            By.CSS_SELECTOR, "#id-dao-ballots tr[data-seat]"
        )
        self.assertEqual(
            [row.get_attribute("data-seat") for row in rows],
            [fakes.SEAT_A, fakes.SEAT_B, fakes.SEAT_C],
        )
        self.assertIn("not voted", rows[1].text)
        self.assertIn("at most", rows[0].text)
        options = self.browser.find_elements(
            By.CSS_SELECTOR, "#id-dao-options tr[data-option]"
        )
        self.assertEqual(len(options), 3)
        self.assertIn("(Abstain)", options[2].text)

    def test_an_open_session_refreshes_its_totals(self):
        self.browser.get(self.server_url + reverse("dao_session", args=[2]))
        live = self.browser.find_element(By.ID, "id-dao-live")
        self.assertEqual(live.get_attribute("hx-trigger"), "every 30s")

    def test_a_passed_session_marks_its_winner(self):
        self.browser.get(self.server_url + reverse("dao_session", args=[1]))
        winner = self.browser.find_element(
            By.CSS_SELECTOR, '#id-dao-options tr[data-option="0"]'
        )
        self.assertIn("winner", winner.text)
        self.assertFalse(
            self.browser.find_element(By.ID, "id-dao-live").get_attribute("hx-trigger")
        )

    def test_the_published_proposal_file_is_served_as_is(self):
        self.browser.get(self.server_url + reverse("dao_session", args=[2]))
        link = self.find_elem_by_link_text("The proposal file as published")
        self.assertTrue(link.get_attribute("href").endswith("/dao/session/2/proposal.md"))

    def test_the_governors_page_lists_every_seat(self):
        self.browser.get(self.server_url + reverse("dao_index"))
        self.find_elem_by_link_text("Governors").click()
        self.wait_for_page_load()
        rows = self.browser.find_elements(
            By.CSS_SELECTOR, "#id-dao-governors tr[data-seat]"
        )
        self.assertEqual(
            [row.get_attribute("data-seat") for row in rows],
            [fakes.SEAT_A, fakes.SEAT_B, fakes.SEAT_C],
        )
        self.assertIn("not voted yet", rows[2].text)


@override_settings(DAO_PROVIDER="")
class DaoPagesWithoutProviderTest(FunctionalTest):
    """A site without the Voting dApp says so instead of failing."""

    def test_the_pages_say_voting_is_not_available(self):
        for name in ("dao_index", "dao_governors"):
            with self.subTest(name=name):
                self.browser.get(self.server_url + reverse(name))
                self.assertTrue(self.browser.find_elements(By.ID, "id-dao-unavailable"))
