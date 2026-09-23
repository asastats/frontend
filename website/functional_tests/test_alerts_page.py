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
from selenium.common.exceptions import StaleElementReferenceException
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

#: The top band, and the only one with nothing to be upsold to.
CLUSTER = SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]


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
        if not elements:
            return ""
        try:
            return elements[0].text
        except StaleElementReferenceException:
            # **Found, then replaced before it could be read.** Every one of
            # these polls runs while htmx is swapping the panel, so the element
            # this found a moment ago may already be detached.
            # `WebDriverWait` ignores `NoSuchElementException` and *not* this,
            # so letting it out fails the wait instead of retrying - the same
            # trap as the waiting finders above, one layer down.
            return ""

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
        one the server does not know. That is what lets the view trust the
        field.

        Counted off `Subject` rather than pinned to a number: a subject added
        to the model and not to the form is the failure worth catching here,
        and a hard-coded count catches "somebody added a subject" instead -
        which is a test that fails on the working case.
        """
        self.sign_in("alerts-subjects@example.com")
        self.open_modal_url()

        options = self.find_elems_by_css(".alerts-subject option")

        assert len(options) == len(Subject.choices)
        assert [option.get_attribute("value") for option in options] == [
            value for value, _ in Subject.choices
        ]

    def test_the_remainder_is_shown_rather_than_the_total(self):
        """The template never subtracts - a second place doing that arithmetic
        is a second place to get it wrong."""
        user = self.sign_in("alerts-left@example.com")
        self.rule(user)
        self.rule(user, threshold="200")

        self.open_modal_url()

        assert "3 of 5 left" in self.find_elem_by_class("alerts-left").text

    def test_a_spent_allowance_says_why_and_where_to_go(self):
        """**"0 of 5 left" needs a sentence beside it.**

        On its own the number reads as something being broken, and the form
        simply vanishing is the only other signal. The reason belongs next to
        the count rather than only where the form used to be - that sentence is
        below the fold on a phone, and is not rendered at all while the reader
        is editing a rule.
        """
        user = self.sign_in("alerts-capped@example.com")
        for threshold in range(1, 6):
            self.rule(user, threshold=str(threshold * 100))

        self.open_modal_url()

        left = self.find_elem_by_class("alerts-left")
        assert "0 of 5 left" in left.text
        assert "a larger plan" in left.text
        assert left.find_element(By.CSS_SELECTOR, "a").get_attribute(
            "href"
        ).endswith("/subscriptions/")

    def test_the_top_tier_is_not_sold_what_it_already_has(self):
        """A Cluster reader at their cap has the largest allowance sold.

        Linking them to the plans page invites them to buy what they own, which
        reads as the site not knowing what they bought.
        """
        user = self.sign_in("alerts-cluster@example.com", permission=CLUSTER)
        for threshold in range(1, 51):
            self.rule(user, threshold=str(threshold * 100))

        self.open_modal_url()

        left = self.find_elem_by_class("alerts-left")
        assert "0 of 50 left" in left.text
        assert "the most any plan keeps" in left.text
        assert left.find_elements(By.CSS_SELECTOR, "a") == []

    def test_a_rule_reads_as_a_sentence_rather_than_a_row(self):
        """**Both halves of what the running site showed a reader.**

        `Portfolio total 86C2B129E807A583C4D37BA182B4EC26F64B3CC9 falls below
        100.0000000000` - a hash of the single address they were looking at,
        and the threshold column's own scale. The page here is one address, so
        it names that address; the threshold is money, so it reads like money.
        """
        user = self.sign_in("alerts-sentence@example.com")
        self.rule(user)

        self.open_modal_url()

        text = self.find_elem_by_class("alerts-rule-text").text
        assert text == (
            f"Portfolio total for {ADDRESS[:5]}...{ADDRESS[-5:]} "
            "falls below 100.00 ALGO"
        )

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

    def test_the_button_is_shown_where_it_belongs_and_not_before(self):
        """**The jump a reader watched on every page load.**

        This partial lands near the top of the page and the button belongs in
        the action row beside Sweep dust, so `placeToolbar` moves it - and a
        move after paint is a visible hop from one row to the next. The partial
        now renders it `hidden` and the script reveals it once it has arrived,
        so the two halves have to hold together: still hidden means a reader
        with no way to reach their alerts, still jumping means the server
        stopped marking it.
        """
        self.sign_in("alerts-placed@example.com")

        self.open_address_page()

        # **Both halves in one condition.** The reveal waits on `alerts.js`
        # finishing its own fetch - the script tag rides in the partial that
        # carries the button - so this is asynchronous by nature. Asserting
        # "in the slot" and "displayed" as two reads would be two looks at a
        # page still settling.
        self.wait_until(
            lambda: self.browser.execute_script(
                "var t = document.getElementById('id-alerts');"
                "return !!(t && !t.hidden && t.parentNode"
                "          && t.parentNode.id === 'id-dustsweep-slot');"
            ),
            timeout=self.OPEN_TIMEOUT,
        )

    def test_editing_a_rule_shows_what_the_asset_costs_now(self):
        """**The reference price had one source: the search results.**

        A row carries `data-usdc-price`, so picking an asset out of the picker
        gave the reader a "Now …" figure to aim at - and the two paths where
        the asset arrives *already chosen* gave them nothing. Editing a rule is
        one of them, and it is the moment a reader is most likely to be
        adjusting a threshold against what the price is doing.

        `resolveAsset` asks the same endpoint the picker asks, by id.
        """
        user = self.sign_in("alerts-reference@example.com")
        self.rule(
            user,
            subject=Subject.ASA_PRICE,
            asset_id=31566704,
            threshold="0.5",
            address=ADDRESS,
        )
        # The endpoint is the swap widget's, and it reaches the engine - which
        # is not running here. The row shape is `swap/_assets.html`'s.
        matches = mock.patch(
            "widgets.inhouse.swapcore.views.fetch_asset_matches",
            return_value=[
                {"id": 31566704, "unit": "USDC", "name": "USDC", "usdc_price": 1.0}
            ],
        )
        matches.start()
        self.addCleanup(matches.stop)

        self.open_address_page()
        self.find_elem_by_css(".id-alerts-open").click()
        self.wait_until(
            lambda: self.text_for(".alerts-edit") != "", timeout=self.OPEN_TIMEOUT
        )
        self.find_elem_by_css(".alerts-edit").click()

        # **The attribute, not the rendered line.** `resolveAsset` owns getting
        # the asset's price onto the page; turning it into "Now 4.00 ALGO" is
        # `showCurrent`, and that needs the page's own ALGO/USD rate - which
        # the live pass publishes and a page in a test has never had. Asserting
        # the text here would be asserting that the *engine* had run.
        #
        # One condition, because the lookup is a fetch and a wait-then-read
        # would be two looks at a settling page.
        self.wait_until(
            lambda: self.browser.execute_script(
                "var n = document.querySelector('.alerts-now');"
                "return n && n.getAttribute('data-asset-usd');"
            )
            == "1.0",
            timeout=self.OPEN_TIMEOUT,
        )

    def test_the_button_counts_what_the_reader_already_keeps(self):
        """**Waits for the reveal, because `.text` is empty until then.**

        The toolbar renders `hidden` and `placeToolbar` moves it into the
        action row and unhides it, so between load and reveal this badge is a
        present element that Selenium reads as "". Read straight after
        `open_address_page` - which waits only for the element to exist - this
        passed alone and failed in a class run, where the page is slower to
        settle than the assertion is to arrive. The count is server-rendered
        and was never wrong; the test was looking too early.
        """
        user = self.sign_in("alerts-entry-count@example.com")
        self.rule(user)

        self.open_address_page()
        self.wait_until(
            lambda: self.browser.execute_script(
                "var t = document.getElementById('id-alerts');"
                "return !!(t && !t.hidden);"
            ),
            timeout=self.OPEN_TIMEOUT,
        )

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
