"""Functional tests for the Dust Sweep widget's page.

Three ways in, all covered here: the standalone tool at
``/widgets/dustsweep/<address>``, the entry on a single address's page, and the
entry on a bundle page - which is the one that has to choose between several of
the reader's own accounts, and the one that got it wrong.

**Almost nothing here signs anything.** The wallet bridge
(``window.asastatsSwap``) ships with the wallet bundle and is absent in a bare
browser, which is exactly the state a reader is in before connecting - and the
state most of these assertions describe. What the page must do without a wallet
is render, name its endpoint, and refuse to offer a sweep of an address the
reader does not own.

The exception is :class:`DustSweepSignatureTest`, which stands a recording stub
in the bridge's place to assert what the controller *hands* it. That is the one
thing no other test could see: the plan is JSON, the bridge takes bytes, and
every layer either side of that conversion was right.

**Why the shell carries so little.** Every decision a sweep makes - what is
dust, what may be forfeited, which group comes next - is made in the engine
against live chain state. If a threshold or an asset list or a creator address
appeared in this markup it would be a value a reader could edit into something
the server then acted on, so the tests below assert their *absence* as firmly
as they assert the plan URL's presence.
"""

from unittest import mock

from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By

from walletauth.models import LinkedAddress

from .base import FunctionalTest

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"


class DustSweepPageTest(FunctionalTest):
    """Load the sweep shell as a reader who owns the address."""

    def _link_address(self, email="dustsweep@example.com"):
        """Log a user in and connect ADDRESS to them, which is what gates a sweep."""
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=100
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
        user.profile.save()

        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        return user

    def _open_page(self):
        self.browser.get(f"{self.server_url}/widgets/dustsweep/{ADDRESS}")
        return self.find_elem_by_id("id-dustsweep")

    def test_the_sweep_page_loads_rather_than_404ing(self):
        """Mounted, which is what makes the URL resolve at all.

        Asserted through the reader's eyes - a heading they can see - rather
        than on a status code, because a Django view can return 200 and render
        an error shell. The asastats widget was discovered by manifest but
        never mounted, and nothing failed loudly; this is the test that would
        have caught the same mistake here.
        """
        self._link_address()
        self._open_page()

        assert "Dust Sweep" in self.find_elem_by_class("dustsweep-page-title").text
        assert "Dust Sweep" in self.browser.title

    def test_the_shell_carries_the_plan_url_the_controller_needs(self):
        """The one endpoint is the whole configuration.

        `dustsweep.js` reads it off the shell; a template that stopped emitting
        it would leave the page looking correct and unable to plan anything.
        """
        self._link_address()
        shell = self._open_page()

        assert shell.get_attribute("data-widget") == "dustsweep"
        assert shell.get_attribute("data-plan-url").endswith("/plan")

    def test_no_sweep_parameter_reaches_the_browser(self):
        """The engine decides; the browser renders.

        A threshold or a creator address in this markup would be a decision a
        reader could edit. Their absence is what keeps the forfeit - the one
        part of a sweep that can take something - entirely server-side.
        """
        self._link_address()
        shell = self._open_page()

        for attribute in (
            "data-threshold",
            "data-creator",
            "data-forfeit",
            "data-assets",
            "data-fee-bps",
        ):
            assert shell.get_attribute(attribute) is None, attribute

    def test_the_owned_address_is_offered_with_its_own_button(self):
        """One row per linked address, each opening the modal for that address.

        A sweep acts on one account at a time - the groups it builds are signed
        by a single holder - so the address travels on the button rather than
        being inferred from the page.
        """
        self._link_address()
        self._open_page()

        rows = self.find_elems_by_css("#id-dustsweep-addresses li[data-address]")
        assert len(rows) == 1
        assert rows[0].get_attribute("data-address") == ADDRESS

        button = rows[0].find_element(By.CSS_SELECTOR, ".id-dustsweep-open")
        assert button.get_attribute("data-address") == ADDRESS

    def test_the_modal_is_closed_until_the_reader_opens_it(self):
        """A native `<dialog>`: closed means not rendered, not merely hidden."""
        self._link_address()
        self._open_page()

        modal = self.find_elem_by_id("dustsweep-modal")
        assert modal.get_attribute("open") is None
        assert not modal.is_displayed()

    def test_opening_the_modal_shows_the_sweep_interface(self):
        """The whole point of this pass: there is an interface to show.

        Asserted through what a reader sees - the modal opens, names the
        address it will sweep, and offers the controls - rather than on
        internal state. Planning itself needs a live engine, which a functional
        test does not have, so the CTA is still in its reading state here.
        """
        self._link_address()
        self._open_page()

        self.find_elem_by_css(".id-dustsweep-open").click()
        modal = self.find_elem_by_id("dustsweep-modal")
        self.wait_until(lambda: modal.get_attribute("open") is not None)

        assert modal.is_displayed()
        assert "Dust Sweep" in self.find_elem_by_css(".dustsweep-title").text
        # the address is named, shortened, so a reader can tell which one
        assert ADDRESS[:6] in self.find_elem_by_css(".id-dustsweep-address-tag").text
        assert self.find_elem_by_css(".id-dustsweep-cta").is_displayed()

    def test_the_modal_closes_again(self):
        """Escape and the close button both have to work, or it is a trap."""
        self._link_address()
        self._open_page()

        self.find_elem_by_css(".id-dustsweep-open").click()
        modal = self.find_elem_by_id("dustsweep-modal")
        self.wait_until(lambda: modal.get_attribute("open") is not None)

        self.find_elem_by_css(".id-dustsweep-close").click()
        self.wait_until(lambda: modal.get_attribute("open") is None)

    def test_the_threshold_control_offers_presets_and_a_custom_field(self):
        """The only input the reader has, and the engine clamps it anyway.

        Low presets because the unsafe direction is upward: a mistyped
        threshold must not be able to reach a balance somebody meant to keep.
        """
        self._link_address()
        self._open_page()
        self.find_elem_by_css(".id-dustsweep-open").click()

        presets = self.find_elems_by_css(".id-dustsweep-threshold-preset")
        assert [one.get_attribute("data-threshold") for one in presets] == [
            "0.1",
            "1",
            "5",
        ]
        assert max(float(one.get_attribute("data-threshold")) for one in presets) <= 10

    def test_the_filter_tabs_default_to_what_will_be_swept(self):
        """A reader opening a sweep wants to see what is about to happen.

        "Everything" exists so a holding the sweep left alone is still
        visible - without it there is no way to tell "kept deliberately" from
        "missed".
        """
        self._link_address()
        self._open_page()
        self.find_elem_by_css(".id-dustsweep-open").click()

        tabs = self.find_elems_by_css("[data-dustsweep-filter]")
        selected = [one for one in tabs if one.get_attribute("aria-selected") == "true"]
        assert len(selected) == 1
        assert selected[0].get_attribute("data-dustsweep-filter") == "sweeping"

    def test_the_page_explains_what_it_recovers_before_anything_is_signed(self):
        """Most of what a sweep returns is minimum balance, not tokens.

        A reader who thinks they are selling dust will judge the result by the
        tokens and conclude it did nothing. The page says so up front, and that
        sentence is part of the product rather than decoration.
        """
        self._link_address()
        self._open_page()

        intro = self.find_elem_by_class("dustsweep-intro").text
        assert "0.1" in intro
        assert "minimum balance" in intro

    def test_the_page_names_no_framework_classes(self):
        """The widget emits semantic hooks; the host paints them.

        Naming a DaisyUI class here would couple the submodule to a framework
        version that changes underneath it, and - because the widget stylesheet
        loads *after* the host's - would override that class for the whole
        page, host chrome included.
        """
        self._link_address()
        shell = self._open_page()

        markup = shell.get_attribute("outerHTML")
        for framework in ('class="btn', '"card"', '"stack"', '"tooltip'):
            assert framework not in markup, framework

        # nor the swap widget's own vocabulary: a sweep is not a swap, and
        # borrowing `swap-*` would tie it to rules changed for swap reasons
        assert "swap-" not in markup

    def test_the_page_loads_without_javascript_errors(self):
        """`dustsweep.js` runs here with no wallet bridge beside it.

        The bridge ships with the wallet bundle and is absent in a bare
        browser. The controller has to tolerate that rather than throwing,
        because it is every reader's state before connecting.
        """
        self._link_address()
        self.record_javascript_errors()
        self._open_page()

        assert self.javascript_errors() == []


class DustSweepPlannedLinesTest(FunctionalTest):
    """What a reader actually reads: the holding rows a plan renders into.

    The engine is stubbed here rather than reached, because none of what is
    asserted is an engine question - the plan's shape is settled by
    ``core.sweep.plan`` and covered by its own tests. What is not covered
    anywhere else is whether the controller *puts it on the screen*, and that
    is a browser question: `renderLine` builds every row in JavaScript, so a
    field the engine sends and the controller drops looks identical in Python.
    """

    PLAN = {
        "address": ADDRESS,
        "threshold_algo": 1.0,
        "summary": {"close": 1, "forfeit": 0, "convert": 0, "recoverable": 100000,
                    "prompts": 1, "unpriced": 0},
        "holdings": [
            {
                "asset": 31566704,
                "unit": "USDC",
                "amount": "0",
                "value": 0,
                "creator": ADDRESS,
                "disposition": "close",
                "reason": "is empty, so closing it returns its 0.1 ALGO",
            },
            {
                "asset": 987654321,
                "unit": None,
                "amount": "5",
                "value": None,
                "creator": ADDRESS,
                "disposition": "unpriced",
                "reason": "has no price, so it is left alone unless you say otherwise",
            },
        ],
        "next": None,
        "refused": [],
        "conversions_unavailable": None,
        "evaluation_unavailable": None,
    }

    _link_address = DustSweepPageTest._link_address
    _open_page = DustSweepPageTest._open_page

    def _open_planned_modal(self):
        """Open the modal with the stub engine answering the plan request."""
        answered = mock.Mock()
        answered.json.return_value = self.PLAN
        with mock.patch(
            "widgets.inhouse.dustsweep.views.engine_request", return_value=answered
        ):
            self.find_elem_by_css(".id-dustsweep-open").click()
            # the plan is fetched after the modal opens, so wait for the rows
            return self.wait_until(
                lambda: self.browser.find_elements(By.CSS_SELECTOR, ".dustsweep-line")
            )

    def test_every_row_names_its_asset_id_beside_the_unit(self):
        """A unit name is not an identity; the asset id is.

        Anyone can mint a second "USDC", and the reader is about to close a
        holding out or give it away. The id is the only thing on the row they
        can check against an explorer first, so it has to be *on* the row -
        not only in the response the row was built from.
        """
        self._link_address()
        self._open_page()
        rows = self._open_planned_modal()

        assert len(rows) == 2
        first = rows[0]
        assert first.find_element(By.CSS_SELECTOR, ".dustsweep-line-unit").text == "USDC"
        assert (
            first.find_element(By.CSS_SELECTOR, ".dustsweep-line-id").text == "#31566704"
        )

    def test_an_unnamed_asset_is_still_identified(self):
        """The rows most worth looking up are the ones with no unit at all.

        `_asset_facts` returns no unit for an asset whose parameters could not
        be read, which used to leave the row labelled with nothing.
        """
        self._link_address()
        self._open_page()
        rows = self._open_planned_modal()

        second = rows[1]
        assert second.find_element(By.CSS_SELECTOR, ".dustsweep-line-unit").text
        assert (
            second.find_element(By.CSS_SELECTOR, ".dustsweep-line-id").text
            == "#987654321"
        )

    def test_the_id_is_visible_rather_than_merely_present(self):
        """A styled-away id is the same as no id.

        The row is a grid; adding a fourth child to a three-column template is
        how a new field ends up wrapped off the visible line.
        """
        self._link_address()
        self._open_page()
        rows = self._open_planned_modal()

        asset_id = rows[0].find_element(By.CSS_SELECTOR, ".dustsweep-line-id")
        unit = rows[0].find_element(By.CSS_SELECTOR, ".dustsweep-line-unit")
        assert asset_id.is_displayed()
        # beside the unit, on the same line, not beneath it
        assert asset_id.location["y"] < unit.location["y"] + unit.size["height"]


class DustSweepSignatureTest(FunctionalTest):
    """What the controller hands the wallet when the reader presses sign.

    The plan is JSON, so its transactions arrive base64-encoded; the bridge's
    ``signAndSend`` takes ``Uint8Array[]`` and passes each entry straight to
    algosdk's ``decodeUnsignedTransaction``. Nothing in between said so, and
    the controller passed the strings through. algosdk turns an array-like of
    characters into one byte each, so a 340-character close-out became 340
    zero bytes and msgpack found a complete object in the first of them::

        RangeError: Extra 339 of 340 byte(s) found at buffer[1]

    Which is a real production failure that named neither base64 nor this
    widget, and which every existing test agreed with: the unit tests mock the
    bridge and asserted the call *as it was made*, and Python cannot see a
    JavaScript argument at all.

    So the bridge is stood up here as a recorder rather than mocked away, and
    what is asserted is the argument's **type**. Its length and its contents
    were both plausible; only the type was wrong.
    """

    _link_address = DustSweepPageTest._link_address
    _open_page = DustSweepPageTest._open_page

    #: An empty holding of asset 5, which closes to the account itself.
    HOLDING = {
        "asset": 5,
        "unit": "DUST",
        "amount": "0",
        "value": 0,
        "creator": ADDRESS,
        "disposition": "close",
        "reason": "already empty, so closing it returns its minimum balance",
    }

    def _encoded_group(self):
        """Return the close-out group as the engine encodes it: base64 msgpack.

        Built with algosdk rather than pasted, because the controller decodes
        it and checks every field against the plan before signing - a fixture
        that drifted from `close_out_group` would be refused by the whitelist
        and the signature would never be reached.
        """
        from algosdk import encoding, transaction

        params = transaction.SuggestedParams(
            fee=1000,
            first=1,
            last=1001,
            gh="SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
            gen="mainnet-v1.0",
            flat_fee=True,
        )
        built = transaction.assign_group_id(
            [
                transaction.AssetTransferTxn(
                    sender=ADDRESS,
                    sp=params,
                    receiver=ADDRESS,
                    amt=0,
                    index=self.HOLDING["asset"],
                    close_assets_to=ADDRESS,
                )
            ]
        )
        return [encoding.msgpack_encode(txn) for txn in built]

    def _plan(self):
        """Return a plan whose next action is one signable close-out group."""
        return {
            "address": ADDRESS,
            "threshold_algo": 1.0,
            "summary": {
                "close": 1,
                "forfeit": 0,
                "convert": 0,
                "keep": 0,
                "unpriced": 0,
                "recoverable": 99000,
                "prompts": 1,
            },
            "holdings": [self.HOLDING],
            "next": {
                "kind": "close",
                "label": "close 1 holding",
                "why": "no pending conversion will produce another close-out",
                "recovers": 99000,
                "remaining_closes": 0,
                "remaining_conversions": 0,
                "holdings": [self.HOLDING],
                "transactions": self._encoded_group(),
            },
            "refused": [],
            "conversions_unavailable": None,
            "evaluation_unavailable": None,
        }

    def _install_recording_bridge(self):
        """Publish a bridge that records the shape of what it is asked to sign.

        Deliberately not a wallet: it records and resolves. What it records is
        `instanceof Uint8Array` per entry, because that is the whole question -
        the real bridge would go on to decode each entry, and it is the decode
        that failed.
        """
        self.browser.execute_script(
            "var address = arguments[0];"
            "window.__signed = null;"
            "window.asastatsSwap = {"
            "  activeAddress: function () { return address; },"
            "  signAndSend: function (group) {"
            "    window.__signed = group.map(function (entry) {"
            "      return {"
            "        bytes: entry instanceof Uint8Array,"
            "        length: entry.length,"
            "        first: entry[0]"
            "      };"
            "    });"
            "    return Promise.resolve('SWEPT');"
            "  }"
            "};"
            "window.dispatchEvent(new CustomEvent('asastats:swap-ready'));",
            ADDRESS,
        )

    def test_the_wallet_is_handed_transaction_bytes(self):
        """Not the base64 they arrived as, which is what the reader hit."""
        self._link_address()
        self._open_page()
        self._install_recording_bridge()

        from base64 import b64decode

        plan = self._plan()
        answered = mock.Mock()
        answered.json.return_value = plan
        with mock.patch(
            "widgets.inhouse.dustsweep.views.engine_request", return_value=answered
        ):
            self.find_elem_by_css(".id-dustsweep-open").click()
            cta = self.wait_until(
                lambda: self.find_elem_by_css(".id-dustsweep-cta").is_enabled()
                and self.find_elem_by_css(".id-dustsweep-cta")
            )
            cta.click()
            signed = self.wait_until(
                lambda: self.browser.execute_script("return window.__signed;")
            )

        encoded = plan["next"]["transactions"][0]
        assert len(signed) == 1
        assert signed[0]["bytes"] is True
        # The decoded size, which is three quarters of the base64 it arrived
        # as. An undecoded group is exactly as long as the string - which is
        # where "340 byte(s)" in the reader's error came from.
        assert signed[0]["length"] == len(b64decode(encoded))
        assert signed[0]["length"] < len(encoded)
        # A msgpack fixmap, so a decoder reads a whole transaction out of it
        # rather than a stray integer followed by bytes it cannot account for.
        assert 0x80 <= signed[0]["first"] <= 0x8F

    def test_a_signed_group_advances_the_loop_rather_than_reporting_an_error(self):
        """The signature is only half of it; the loop asks again afterwards.

        Where the failure this class exists for became *visible*: the
        controller renders whatever the bridge throws into the notice line, so
        a wrong argument and a declined signature read the same to a reader.
        This test cannot reproduce it - the stub records rather than decodes,
        which is why its sibling asserts on the argument's type instead - so
        what it holds is the other half: that a group the wallet accepted
        advances the loop and leaves no error behind.

        Asserted on the progress line rather than on the success notice, which
        `reload` clears as soon as it asks the engine what is next.
        """
        self._link_address()
        self._open_page()
        self._install_recording_bridge()

        answered = mock.Mock()
        answered.json.return_value = self._plan()
        with mock.patch(
            "widgets.inhouse.dustsweep.views.engine_request", return_value=answered
        ):
            self.find_elem_by_css(".id-dustsweep-open").click()
            cta = self.wait_until(
                lambda: self.find_elem_by_css(".id-dustsweep-cta").is_enabled()
                and self.find_elem_by_css(".id-dustsweep-cta")
            )
            cta.click()
            progress = self.wait_until(
                lambda: self.find_elem_by_css(".id-dustsweep-progress").text
                == "Signature 2 of 2"
            )

        assert progress
        assert self.find_elem_by_css(".id-dustsweep-notice").text == ""


class DustSweepPageUnlinkedTest(FunctionalTest):
    """A reader who does not own the address is told, not offered a sweep."""

    def test_an_unlinked_reader_is_told_to_connect_rather_than_shown_a_panel(self):
        """Ownership gates the panel, and the message has to be visible.

        Stronger here than on a swap page: a sweep reads a whole account and
        returns a group that closes its holdings out. The locked notice and the
        address list are mutually exclusive in the template, and asserting both
        directions is what stops a future edit rendering the panel for someone
        who does not own the address.
        """
        session_cookie = self.create_session_cookie(
            username="dustsweep-unlinked@example.com",
            password="top_secret",
            permission=100,
        )
        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        self.browser.get(f"{self.server_url}/widgets/dustsweep/{ADDRESS}")

        locked = self.find_elem_by_id("id-dustsweep-locked")
        assert locked.is_displayed()
        assert "Connect the wallet" in locked.text

        # `find_elems_by_css` waits for presence *before* returning the list,
        # so it can never express absence - asked for something that is not
        # there it times out rather than returning []. The driver's own
        # `find_elements` returns an empty list immediately, which is the only
        # way to assert a thing is missing.
        assert (
            self.browser.find_elements(
                By.CSS_SELECTOR, "#id-dustsweep-addresses li[data-address]"
            )
            == []
        )


class DustSweepAddressPageEntryTest(FunctionalTest):
    """The entry point: reaching the sweep from the address page.

    The address page is ``cache_page``'d across users, so this arrives through
    the same non-cached htmx partial the swap entry uses. That is not an
    optimisation - rendering "is this address yours?" into the shared page
    would serve one reader's answer to everyone who came after.
    """

    def _link_address(self, email="dustsweep-entry@example.com"):
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=100
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
        user.profile.preferred_router = "folks"
        user.profile.save()

        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        return user

    def _connect(self, address):
        """Publish a wallet bridge connected to `address`, as the bundle does.

        The real bridge ships with the wallet package and needs a wallet
        extension and a signature to reach this state; what the sweep entry
        reads off it is one method, so that is what is stood up here. The
        ready event is dispatched too, because that is the path a reader who
        connects during page load takes.
        """
        self.browser.execute_script(
            "var address = arguments[0];"
            "window.asastatsSwap = {"
            "  activeAddress: function () { return address; }"
            "};"
            "window.dispatchEvent(new CustomEvent('asastats:swap-ready'));",
            address,
        )

    def test_the_sweep_is_not_offered_until_a_wallet_is_connected(self):
        """The entry waits for the account it would act on.

        A sweep is signed by one key. Until the browser says which account the
        wallet holds, there is no address to build a group for - so the button
        is rendered and hidden rather than pointed at a guess, because a guess
        is only discovered to be wrong at the signature prompt.
        """
        self._link_address()
        self.browser.get(f"{self.server_url}/{ADDRESS}")

        # Present, because connecting must not need another round trip...
        self.find_elem_by_id("id-swap-entry-container")
        button = self.wait_until(
            lambda: self.browser.find_elements(By.CSS_SELECTOR, ".id-dustsweep-open")
        )[0]
        # ...and hidden, because there is nothing it could sweep yet.
        assert not button.is_displayed()

    def test_connecting_a_wallet_offers_the_sweep_for_that_account(self):
        """The whole point of an entry point: it can be found without a URL."""
        self._link_address()
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.find_elem_by_id("id-swap-entry-container")
        self._connect(ADDRESS)

        button = self.wait_until(
            lambda: self.find_elem_by_css(".id-dustsweep-open").is_displayed()
            and self.find_elem_by_css(".id-dustsweep-open")
        )
        assert "Sweep" in button.text
        assert button.get_attribute("data-address") == ADDRESS

    def test_the_sweep_sits_with_the_pages_other_actions(self):
        """Beside Historic data and CSV export, not in a band of its own.

        It arrives in the htmx partial - the address page's cache entry is
        shared, so nothing per-reader may be rendered into the page itself -
        and the controller moves it into the slot the template reserves. The
        assertion is on where it ended up, because that is what a reader sees.
        """
        self._link_address()
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.find_elem_by_id("id-swap-entry-container")
        self._connect(ADDRESS)
        self.wait_until(
            lambda: self.find_elem_by_css(".id-dustsweep-open").is_displayed()
        )

        assert self.browser.find_elements(
            By.CSS_SELECTOR, "#id-dustsweep-slot .id-dustsweep-open"
        )

    def test_the_sweep_is_as_tall_as_the_actions_beside_it(self):
        """One row of controls, not two controls and an intruder.

        It keeps its filled pill on purpose - it opens a modal where the other
        two leave the page - but the *box* has to line up, and a button sized
        by its own padding did not: it stood a third of a line proud of them.
        Measured in the browser rather than asserted against the rule, because
        the neighbours' height comes from theme tokens (``--size-field``,
        ``--border``) and only a measurement notices those moving.
        """
        self._link_address()
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.find_elem_by_id("id-swap-entry-container")
        self._connect(ADDRESS)
        self.wait_until(
            lambda: self.find_elem_by_css(".id-dustsweep-open").is_displayed()
        )

        sweep = self.find_elem_by_css("#id-dustsweep-slot .id-dustsweep-open")
        neighbours = [
            elem
            for elem in self.browser.find_elements(By.CSS_SELECTOR, "a.btn-sm")
            if elem.text.strip() in ("Historic data", "CSV export")
        ]
        assert neighbours, "the actions this one is meant to match are not there"
        for neighbour in neighbours:
            with self.subTest(action=neighbour.text.strip()):
                assert sweep.size["height"] == neighbour.size["height"]

    def test_the_sweep_opens_from_the_address_page(self):
        """It is wired there too, not merely rendered."""
        self._link_address()
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.find_elem_by_id("id-swap-entry-container")
        self._connect(ADDRESS)
        self.wait_until(
            lambda: self.find_elem_by_css(".id-dustsweep-open").is_displayed()
        )

        self.find_elem_by_css(".id-dustsweep-open").click()
        modal = self.find_elem_by_id("dustsweep-modal")
        self.wait_until(lambda: modal.get_attribute("open") is not None)
        assert modal.is_displayed()

    def test_switching_account_withdraws_the_offer(self):
        """Connected is not enough; it has to be connected to *this* page.

        A reader who switches their wallet to an account this page does not
        show can no longer sign a sweep of it, so the offer goes away again.
        Asserted by watching it appear first: a button that was never shown
        would pass the second half on its own and prove nothing.

        This is also what the entry's polling is for. The wallet package
        publishes one event, at bootstrap, and says nothing when the reader
        connects or switches afterwards - so an entry that read the bridge once
        would be stuck on whatever was true when the page happened to load.
        """
        self._link_address()
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.find_elem_by_id("id-swap-entry-container")

        self._connect(ADDRESS)
        self.wait_until(
            lambda: self.find_elem_by_css(".id-dustsweep-open").is_displayed()
        )

        self._connect("VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU")
        self.wait_until(
            lambda: not self.find_elem_by_css(".id-dustsweep-open").is_displayed()
        )

    def test_an_unlinked_reader_is_offered_nothing(self):
        """The gate is ownership, and it is applied server-side.

        Not hidden with CSS: the markup must not be there at all, because a
        button that appears for everyone and works for nobody is worse than no
        button.
        """
        session_cookie = self.create_session_cookie(
            username="dustsweep-nolink@example.com",
            password="top_secret",
            permission=100,
        )
        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        self.browser.get(f"{self.server_url}/{ADDRESS}")

        # let the htmx partial land before concluding it rendered nothing
        self.find_elem_by_id("id-swap-entry-container")
        assert self.browser.find_elements(By.CSS_SELECTOR, ".id-dustsweep-open") == []


class DustSweepBundlePageEntryTest(FunctionalTest):
    """Reaching the sweep from a *bundle* page, which is where it went wrong.

    A bundle page shows several addresses consolidated, and a sweep is signed
    by one holder's key. Two wrong answers came before this one. The first
    picked whichever of the reader's addresses sorted first and said nothing
    about it, so a reader whose wallet was on the other one got a group that
    account cannot sign. The second offered a button *each* and let the reader
    choose - which is the same failure with the blame moved, because the reader
    cannot sign for an account their wallet is not on either.

    The answer is that only one of them is ever offerable, and the browser is
    the only place that knows which: the server publishes the candidates and
    the controller matches them against the live wallet.
    """

    OTHER = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
    THIRD = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M"
    BUNDLE = "540A5D8CEC896E073F9170AF0A962503E69147CF"

    def _link(self, addresses, primary, email="dustsweep-bundle@example.com"):
        """Connect every address in `addresses`, making `primary` the primary."""
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=100
        )
        user = get_user_model().objects.get(username=email)
        for one in addresses:
            LinkedAddress.objects.create(
                profile=user.profile,
                address=one,
                canonical_address=one,
                chain="algorand",
                auth_method="algorand_wallet",
                is_primary=one == primary,
                login_enabled=True,
            )
        user.profile.address = primary
        user.profile.save()

        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        return user

    def _connect(self, address):
        """Publish a wallet bridge connected to `address`. See the entry test."""
        self.browser.execute_script(
            "var address = arguments[0];"
            "window.asastatsSwap = {"
            "  activeAddress: function () { return address; }"
            "};"
            "window.dispatchEvent(new CustomEvent('asastats:swap-ready'));",
            address,
        )

    def _open_bundle(self, addresses, connected=None):
        """Load the bundle page, optionally with a wallet already connected.

        The patch has to cover the htmx partial as well as the page: the
        partial is a second request, and it is the one that resolves the
        bundle into addresses.
        """
        with mock.patch(
            "core.views.check_bundle_addresses", return_value=" ".join(addresses)
        ):
            self.browser.get(f"{self.server_url}/{self.BUNDLE}")
            self.find_elem_by_id("id-swap-entry-container")
            buttons = self.wait_until(
                lambda: self.browser.find_elements(
                    By.CSS_SELECTOR, ".id-dustsweep-open"
                )
            )
            if connected:
                self._connect(connected)
                self.wait_until(
                    lambda: self.find_elem_by_css(".id-dustsweep-open").is_displayed()
                )
            return buttons

    def test_only_the_connected_account_is_offered(self):
        """Three addresses on the page, two of them theirs, one button.

        The other owned address is a real address the reader really controls -
        and still not offerable, because the wallet holds one account at a time
        and a group built for the other one cannot be signed.
        """
        self._link([ADDRESS, self.OTHER], primary=ADDRESS)
        buttons = self._open_bundle(
            [ADDRESS, self.OTHER, self.THIRD], connected=self.OTHER
        )

        assert len(buttons) == 1
        assert buttons[0].get_attribute("data-address") == self.OTHER

    def test_the_button_names_the_account_it_will_sweep(self):
        """On a bundle the reader is owed which of their accounts this is.

        Not on a single-address page: there the label would repeat the address
        the page is already about, so the span is not rendered at all.
        """
        self._link([ADDRESS, self.OTHER], primary=ADDRESS)
        buttons = self._open_bundle([ADDRESS, self.OTHER], connected=self.OTHER)

        assert self.OTHER[:6] in buttons[0].text
        assert self.OTHER[-4:] in buttons[0].text

    def test_the_modal_opens_on_the_connected_account(self):
        """The bug, asserted end to end.

        The primary address is ADDRESS and the wallet is on OTHER, so the two
        disagree - and the sweep has to follow the wallet, which is the half
        that will be asked for a signature.
        """
        self._link([ADDRESS, self.OTHER], primary=ADDRESS)
        buttons = self._open_bundle([ADDRESS, self.OTHER], connected=self.OTHER)
        buttons[0].click()

        modal = self.find_elem_by_id("dustsweep-modal")
        self.wait_until(lambda: modal.get_attribute("open") is not None)
        tag = self.find_elem_by_css(".id-dustsweep-address-tag").text
        assert self.OTHER[:6] in tag
        assert self.OTHER[-4:] in tag

    def test_a_wallet_on_none_of_the_bundles_addresses_is_offered_nothing(self):
        """Owning an address the page does not show is not enough either."""
        self._link([ADDRESS, self.OTHER], primary=ADDRESS)
        buttons = self._open_bundle([ADDRESS, self.OTHER])
        self._connect(self.THIRD)

        assert not buttons[0].is_displayed()

    def test_a_reader_who_owns_none_of_the_bundle_is_offered_nothing(self):
        """"If the connected address isn't in the bundle, no action is possible."."""
        self._link([self.THIRD], primary=self.THIRD)
        with mock.patch(
            "core.views.check_bundle_addresses",
            return_value=f"{ADDRESS} {self.OTHER}",
        ):
            self.browser.get(f"{self.server_url}/{self.BUNDLE}")
            self.find_elem_by_id("id-swap-entry-container")
            assert (
                self.browser.find_elements(By.CSS_SELECTOR, ".id-dustsweep-open") == []
            )
