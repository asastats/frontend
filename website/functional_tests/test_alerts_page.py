"""Functional tests for the Alerts widget.

**What only a browser can answer here.** The Python suite covers every view and
the jest suite covers `alerts.js` against a hand-built DOM, and between them
they still cannot see the three things this widget is actually made of: that the
control fetches a modal over htmx, that a native ``<dialog>`` opens when it
arrives, and that the form's fields appear and disappear as the subject changes
- on markup the server rendered rather than markup a test wrote.

Two ways in, both here: the modal at its own URL ``/widgets/alerts/<page>``,
which needs no engine, and the control on the address page, which needs every
engine call mocked - see :class:`AddressPageEngineMixin` in
``test_dustsweep_page.py``, whose docstring explains why that mock is the
difference between twelve broken tests and one missing patch.

**Nothing here subscribes a browser to push.** That needs a real push service
and a permission prompt, and a headless Chrome has neither. What the page must
do *without* one - render the enable control, and say plainly when this
deployment cannot send at all - is what the assertions below describe.
"""

import json
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from selenium.webdriver.common.by import By

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from walletauth.models import LinkedAddress
from widgets.inhouse.alerts.models import AlertRule, Direction, Subject

from .base import COOKIE_SEED_URL, FunctionalTest

#: The serialized account the address page renders from, as the sweep's own
#: functional tests use it. These tests care about the alerts control rather
#: than the figures, so any real payload does.
SAMPLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "utils",
    "tests",
    "sample_serialized_540A5.json",
)

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

#: Asastatser is the first tier that admits a rule at all - Trial and Intro get
#: none - which makes it the boundary every gating assertion here sits on.
ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
INTRO = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]


class AlertsReaderMixin:
    """Sign a reader in at a chosen tier, with ADDRESS linked to them."""

    def sign_in(self, email, permission=ASASTATSER):
        """Return a signed-in user whose profile sits at `permission`."""
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=permission
        )
        user = get_user_model().objects.get(username=email)
        LinkedAddress.objects.create(
            profile=user.profile,
            address=ADDRESS,
            canonical_address=ADDRESS,
            chain="algorand",
            auth_method="algorand_wallet",
            is_primary=True,
            login_enabled=True,
        )
        user.profile.address = ADDRESS
        # `create_session_cookie` sets the permission it was given; the tier is
        # read off the profile, so it is written here rather than assumed.
        user.profile.permission = permission
        user.profile.save()

        self.browser.get(self.server_url + COOKIE_SEED_URL)
        self.browser.add_cookie(session_cookie)
        return user

    def rule(self, user, **overrides):
        """Store one rule for `user` on ADDRESS."""
        fields = {
            "user": user,
            "subject": Subject.TOTAL_VALUE,
            "direction": Direction.DOWN,
            "threshold": "100",
            "address": ADDRESS,
        }
        fields.update(overrides)
        return AlertRule.objects.create(**fields)

    def text_for(self, selector):
        """Return the first `selector`'s text, or "" when there is none.

        **Used inside every `wait_until` predicate here, in place of the
        waiting finders.** `find_elem_by_*` blocks for five seconds and raises
        `TimeoutException`, which `WebDriverWait` does not ignore - so a
        predicate built on one fails the outer wait rather than retrying, and
        an htmx swap that was merely slow reads as a swap that never happened.
        """
        elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
        return elements[0].text if elements else ""

    def open_modal_url(self):
        """Load the modal at its own URL and open it, which needs no engine.

        **The dialog has to be opened explicitly here, and that is not a
        workaround.** This URL answers the htmx fragment; reached directly it
        renders a closed `<dialog>`, because what normally opens one is
        `alerts.js` reacting to the swap - which has not happened. A closed
        dialog is `display:none`, so every element inside it reports empty text
        and a passing assertion would only mean the markup exists somewhere.

        The swap path is covered where it belongs, in
        :class:`AlertsAddressPageEntryTest`.
        """
        self.browser.get(f"{self.server_url}/widgets/alerts/{ADDRESS}")
        panel = self.find_elem_by_id("id-alerts-panel")
        self.browser.execute_script(
            "var d = document.getElementById('alerts-modal');"
            "if (d && !d.open) d.showModal();"
        )
        return panel


class AddressPageMixin(AlertsReaderMixin):
    """Load the real address page, with every engine call it makes mocked.

    **The script only exists here.** `alerts.js` is loaded by
    `_swap_entry.html`, the per-reader partial that carries the control - not
    by the modal. Reached at its own URL the modal is markup with no behaviour,
    so anything about *reacting* to a reader has to come through this page.

    Unmocked, the address page 500s: on CI there is no engine and locally the
    deployment credential is rejected. `#id-alerts` would never render and
    every test here would time out waiting for it, which reads as a broken
    widget rather than a missing patch.
    """

    #: Longer than the default five seconds, and measured rather than guessed.
    #:
    #: Pressing the control is a fetch, a swap and a `showModal()` on top of an
    #: address page carrying a full account, and each test starts its own
    #: browser. Run as a class on this hardware the chain passes five seconds
    #: often enough to matter.
    OPEN_TIMEOUT = 30

    def setUp(self):
        super().setUp()
        patches = [
            mock.patch("core.context_processors.fetch_capabilities"),
            mock.patch("core.views.check_export_status"),
            mock.patch("core.views.fetch_and_serialize_account"),
        ]
        capabilities, status, account = [patch.start() for patch in patches]
        for patch in patches:
            self.addCleanup(patch.stop)
        capabilities.return_value = {"permission": 100}
        status.return_value = {}
        with open(SAMPLE_PATH) as sample_file:
            account.return_value = json.load(sample_file)

    def open_address_page(self):
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        return self.find_elem_by_id("id-alerts")

    def dialog_is_open(self):
        return self.browser.execute_script(
            "var d = document.getElementById('alerts-modal');"
            "return Boolean(d && d.open);"
        )

    def choose_subject(self, subject):
        """Pick `subject` and let the delegated change handler run."""
        select = self.find_elem_by_css(".alerts-subject")
        self.browser.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            select,
            subject,
        )

    def fill_form(self, subject="total_value", threshold="100", asset_id=None):
        """Complete the form the way a reader would, then leave it ready to save.

        **A subject and a threshold at minimum.** The first option in the
        select is `asa_price`, which also needs an asset - so pressing save on
        an untouched form is a *rejected* rule, not a written one, and a test
        that did that would be asserting on the error path by accident.
        """
        self.choose_subject(subject)
        self.browser.execute_script(
            "var form = document.querySelector('.alerts-form');"
            "form.querySelector('[name=threshold]').value = arguments[0];"
            "if (arguments[1] !== null) {"
            "  form.querySelector('[name=asset_id]').value = arguments[1];"
            "}",
            threshold,
            asset_id,
        )

    def save_form(self):
        self.find_elem_by_css(".alerts-save").click()

    def open_modal_from_button(self):
        """Wait for the script, press the control, wait for the dialog.

        **The wait for `window.asastatsAlerts` is the whole point of it.**
        `alerts.js` is loaded by a tag inside the per-reader partial, which is
        itself swapped in, so there is a window where the button exists and
        nothing is listening for the swap it triggers. A press in that window
        fetches the modal and leaves it closed - which is what a reader would
        see, and what made these tests pass alone and fail in company.
        """
        self.open_address_page()
        self.wait_until(
            lambda: self.browser.execute_script(
                "return Boolean(window.asastatsAlerts);"
            ),
            timeout=self.OPEN_TIMEOUT,
        )
        self.find_elem_by_css(".id-alerts-open").click()
        self.wait_until(self.dialog_is_open, timeout=self.OPEN_TIMEOUT)


class AlertsModalTest(AlertsReaderMixin, FunctionalTest):
    """The modal itself, fetched at its own URL."""

    def test_the_modal_renders_for_an_entitled_reader(self):
        """Mounted and reachable, which is what makes the URL resolve.

        Asserted through what a reader sees rather than on a status code: a
        Django view can answer 200 and render an error shell, and a widget that
        is discovered by manifest but never mounted fails exactly that quietly.
        """
        self.sign_in("alerts-modal@example.com")

        self.open_modal_url()

        assert self.find_elem_by_class("alerts-title").text == "Alerts"

    def test_the_form_offers_every_subject_the_server_knows(self):
        """**Server-rendered, so anything else a browser posts was typed.**

        The form's choices come from `Subject.choices`; a reader cannot invent
        a fifth. That is what lets the view trust the field.
        """
        self.sign_in("alerts-subjects@example.com")
        self.open_modal_url()

        options = self.find_elems_by_css(".alerts-subject option")

        assert len(options) == 4

    def test_the_remainder_is_shown_rather_than_the_total(self):
        """The template never subtracts - a second place doing that arithmetic
        is a second place to get it wrong."""
        user = self.sign_in("alerts-left@example.com")
        self.rule(user)
        self.rule(user, threshold="200")

        self.open_modal_url()

        assert "3 of 5 left" in self.find_elem_by_class("alerts-left").text

    def test_a_kept_rule_is_listed_with_a_way_to_remove_it(self):
        user = self.sign_in("alerts-listed@example.com")
        self.rule(user)

        self.open_modal_url()

        rules = self.find_elems_by_class("alerts-rule")
        assert len(rules) == 1
        assert rules[0].find_element(By.CSS_SELECTOR, ".alerts-remove")

    def test_a_reader_with_no_rules_is_told_so(self):
        self.sign_in("alerts-empty@example.com")

        self.open_modal_url()

        assert "No alerts yet" in self.find_elem_by_class("alerts-empty").text


class AlertsFieldsTest(AddressPageMixin, FunctionalTest):
    """Which fields a subject needs, on server-rendered markup.

    The jest suite covers `syncFields` against a DOM it wrote itself. What it
    cannot check is that the template still emits the classes the function
    looks for, and that the script is on the page at all - so these run through
    the address page, which is where `alerts.js` is loaded.
    """

    def _hidden(self, selector):
        """Whether `selector` is currently hidden, read fresh each time.

        **Polled rather than sampled.** The modal opens and syncs its fields on
        a swap, and the page it opens over is swapping fragments of its own -
        live refresh re-renders every block. Reading the attribute once, in the
        instant after dispatching `change`, passes alone and fails in a class,
        which is the shape of every flaky browser test ever written.
        """
        elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
        return bool(elements) and bool(elements[0].get_attribute("hidden"))

    def _wait_hidden(self, selector, hidden=True):
        self.wait_until(
            lambda: self._hidden(selector) is hidden, timeout=self.OPEN_TIMEOUT
        )

    def test_a_portfolio_subject_asks_for_neither_asset_nor_period(self):
        self.sign_in("alerts-fields-total@example.com")
        self.open_modal_from_button()

        self.choose_subject("total_value")

        self._wait_hidden(".alerts-asset-field")
        self._wait_hidden(".alerts-window-field")

    def test_an_asset_subject_asks_for_an_asset(self):
        self.sign_in("alerts-fields-asset@example.com")
        self.open_modal_from_button()

        self.choose_subject("asa_price")

        self._wait_hidden(".alerts-asset-field", hidden=False)
        self._wait_hidden(".alerts-window-field")

    def test_a_percentage_subject_asks_for_a_period(self):
        self.sign_in("alerts-fields-percent@example.com")
        self.open_modal_from_button()

        self.choose_subject("total_percent")

        self._wait_hidden(".alerts-window-field", hidden=False)
        self._wait_hidden(".alerts-asset-field")

    def test_the_warm_up_line_appears_with_the_period(self):
        """**Said before they choose, not after they wait.**

        A percentage rule reports nothing until it has a window of history, so
        a reader picking "7 days" hears nothing for a week. The note lives
        inside the period label so it is revealed with the control; moved out,
        it would sit under every subject explaining a field that is not there.
        """
        self.sign_in("alerts-warmup@example.com")
        self.open_modal_from_button()

        self.choose_subject("total_percent")

        self._wait_hidden(".alerts-window-field", hidden=False)
        note = self.find_elem_by_css(".alerts-window-note")
        assert note.is_displayed()
        assert "history" in note.text


class AlertsWritingTest(AddressPageMixin, FunctionalTest):
    """Creating and removing a rule, which is htmx swapping a server-rendered
    panel in place rather than any JavaScript drawing a list.

    **Through the address page, because the standalone modal URL has no htmx.**
    That URL answers a fragment; htmx and `alerts.js` are both loaded by the
    page the fragment is swapped into. Submitting the form there is an ordinary
    POST that navigates away - which is a fair description of what a reader
    would get if the script ever failed to load, and not what these tests are
    about.
    """

    def test_writing_a_rule_puts_it_in_the_list(self):
        self.sign_in("alerts-create@example.com")
        self.open_modal_from_button()
        self.fill_form()

        self.save_form()

        self.wait_until(
            lambda: "Portfolio total" in self.text_for(".alerts-rule-text"),
            timeout=self.OPEN_TIMEOUT,
        )

    def test_writing_a_rule_spends_one_of_the_allowance(self):
        self.sign_in("alerts-spend@example.com")
        self.open_modal_from_button()
        assert "5 of 5 left" in self.find_elem_by_class("alerts-left").text
        self.fill_form()

        self.save_form()

        self.wait_until(
            lambda: "4 of 5 left" in self.text_for(".alerts-left"),
            timeout=self.OPEN_TIMEOUT,
        )

    def test_a_rejected_rule_says_why_and_keeps_the_form(self):
        """**422 rather than 400**, which is what htmx's error handling
        distinguishes - and the panel it answers with carries the message."""
        self.sign_in("alerts-invalid@example.com")
        self.open_modal_from_button()
        self.fill_form(threshold="0")
        self.browser.execute_script(
            "document.querySelector('[name=threshold]').removeAttribute('min');"
        )

        self.save_form()

        self.wait_until(
            lambda: "more than zero" in self.text_for(".alerts-error"),
            timeout=self.OPEN_TIMEOUT,
        )

    def test_removing_a_rule_takes_it_out_of_the_list(self):
        user = self.sign_in("alerts-remove@example.com")
        self.rule(user)
        self.open_modal_from_button()

        self.find_elem_by_css(".alerts-remove").click()

        self.wait_until(
            lambda: "No alerts yet" in self.text_for(".alerts-empty"),
            timeout=self.OPEN_TIMEOUT,
        )

    def test_at_the_limit_the_form_is_gone_rather_than_disabled(self):
        """A reader who has spent their allowance is told, not handed a control
        that refuses them."""
        user = self.sign_in("alerts-full@example.com")
        for index in range(5):
            self.rule(user, threshold=f"{index + 1}00")

        self.open_modal_from_button()

        assert "0 of 5 left" in self.find_elem_by_class("alerts-left").text
        assert self.browser.find_elements(By.CSS_SELECTOR, ".alerts-form") == []


class AlertsDeploymentNoticeTest(AlertsReaderMixin, FunctionalTest):
    """What the modal says about *this deployment* rather than about a reader."""

    @override_settings(ALERTS_WEBHOOK_SECRET="")
    def test_a_site_that_cannot_send_says_so(self):
        """Without the shared secret both receiving endpoints refuse every
        call, so no rule can fire however complete the code is. Taking rules
        without saying that is a promise the deployment does not keep."""
        self.sign_in("alerts-notice-off@example.com")

        self.open_modal_url()

        assert "not switched on" in self.find_elem_by_class("alerts-note").text

    @override_settings(ALERTS_WEBHOOK_SECRET="configured-for-this-test")
    def test_a_configured_site_carries_no_notice(self):
        self.sign_in("alerts-notice-on@example.com")

        self.open_modal_url()

        assert self.browser.find_elements(By.CSS_SELECTOR, ".alerts-note") == []


class AlertsPushControlTest(AlertsReaderMixin, FunctionalTest):
    """The enable control, as far as a headless browser can see it."""

    def test_the_public_key_reaches_the_browser_and_the_private_one_does_not(self):
        """A subscription is bound to the public key, so the browser must have
        it. The private one signs and never leaves the server - asserted on the
        whole page, because a leak would not be in the element that should
        carry it."""
        self.sign_in("alerts-vapid@example.com")
        self.open_modal_url()

        enable = self.find_elem_by_css(".alerts-enable")
        source = self.browser.page_source

        assert enable.get_attribute("data-vapid-key") is not None
        assert "VAPID_PRIVATE_KEY" not in source
        assert "vapid_private" not in source.lower()


class AlertsAddressPageEntryTest(AddressPageMixin, FunctionalTest):
    """The control on the address page, and the tier that decides its shape.

    The address page is ``cache_page``'d across readers, so this arrives
    through the same per-reader htmx partial the swap and sweep entries use.
    That is not an optimisation: rendering "how many alerts do *you* have left"
    into the shared page would serve one reader's answer to everyone after.
    """

    def test_an_entitled_reader_gets_a_button_naming_their_page(self):
        self.sign_in("alerts-entry@example.com")

        toolbar = self.open_address_page()

        assert toolbar.get_attribute("data-bundle") == ADDRESS
        assert toolbar.get_attribute("data-rules-left") == "5"
        assert self.find_elem_by_css(".id-alerts-open")

    def test_the_button_counts_what_the_reader_already_keeps(self):
        user = self.sign_in("alerts-entry-count@example.com")
        self.rule(user)

        self.open_address_page()

        assert self.find_elem_by_class("alerts-count").text == "1"

    def test_below_the_tier_it_is_an_upgrade_link_not_a_dead_button(self):
        """**A disabled control teaches a reader the feature is broken.**

        Intro gets no rules, so the gate is real - but the answer to "you
        cannot do this yet" is the page that sells it, not a button that does
        nothing when pressed.
        """
        self.sign_in("alerts-intro@example.com", permission=INTRO)

        self.open_address_page()

        upgrade = self.find_elem_by_css(".alerts-upgrade")
        assert "subscriptions" in upgrade.get_attribute("href")
        assert self.browser.find_elements(By.CSS_SELECTOR, ".id-alerts-open") == []

    def test_at_the_limit_the_button_says_so_to_the_script(self):
        user = self.sign_in("alerts-entry-full@example.com")
        for index in range(5):
            self.rule(user, threshold=f"{index + 1}00")

        self.open_address_page()

        button = self.find_elem_by_css(".id-alerts-open")
        assert button.get_attribute("data-at-limit") == "true"

    def test_pressing_the_button_opens_the_dialog(self):
        """**The one thing neither other suite can see.** The control fetches
        the modal over htmx, and `alerts.js` opens it on the swap - a native
        `<dialog>` is closed until `showModal()` is called, so a modal that
        arrives and never opens looks like a button that does nothing.
        """
        self.sign_in("alerts-entry-open@example.com")
        self.open_address_page()

        self.find_elem_by_css(".id-alerts-open").click()

        self.wait_until(self.dialog_is_open, timeout=self.OPEN_TIMEOUT)

    def test_the_dialog_closes_again(self):
        self.sign_in("alerts-entry-close@example.com")
        self.open_address_page()
        self.open_modal_from_button()

        self.find_elem_by_css(".id-alerts-close").click()

        self.wait_until(
            lambda: not self.dialog_is_open(), timeout=self.OPEN_TIMEOUT
        )

    def test_an_anonymous_reader_gets_no_alerts_control_at_all(self):
        """Not an upgrade link either: there is nobody to upgrade."""
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.find_elem_by_id("id-swap-entry-container")

        assert self.browser.find_elements(By.CSS_SELECTOR, "#id-alerts") == []
