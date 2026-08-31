const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.resolve(__dirname, './index.html'), 'utf8');
const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

// No Materialize import and no plugin stubs: the framework is gone from the
// project, so these suites run in the same bare environment a real page has.
const site = require('../static/js/site.js');

jest
  .dontMock('fs');

beforeEach(() => {
  document.documentElement.innerHTML = html.toString();
  site.mainSite();
});

afterEach(() => {
  jest.resetModules();
});


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Structure
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("in rendered index html", function () {
  describe("footer links exist", function () {
    it('for X/Twitter', function () {
      expect($('a[href*="x.com"]').length).toBeGreaterThan(0);
    });
    it('for Discord', function () {
      expect($('a[href*="discord.gg"]').length).toBeGreaterThan(0);
    });
    it('for Reddit', function () {
      expect($('a[href*="reddit.com"]').length).toBeGreaterThan(0);
    });
  });
});


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Initialization
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("in SECTION: Initialization", function () {

  // mainSite
  describe("mainSite function", function () {
    it('binds copy-to-clipboard', function () {
      // The index fixture carries no `.copy` control, so one is added here.
      document.body.insertAdjacentHTML(
        "beforeend", '<a class="copy" href="#">Copy</a>'
      );
      site.mainSite();
      expect(getEvents($(".copy")[0]).click[0].handler.name)
        .toBe("copyToClipboard");
    });

    it('delegates the swap gate from the document', function () {
      site.mainSite();
      var events = getEvents(document);
      expect(events.click.some(function (e) {
        return e.handler.name === "swapLoginGate";
      })).toBe(true);
    });

    // mainSite runs inside jQuery's ready queue, and a callback that throws
    // abandons the rest of the queue -- taking every other page script down
    // with it. That is how home-page sorting and filtering came to be silently
    // inert. Materialize is gone from the project entirely now, so the point
    // is that mainSite reaches its last line with nothing of it present.
    it('does not throw with no Materialize on the page', function () {
      expect(typeof window.M).toBe("undefined");
      expect(function () { site.mainSite(); }).not.toThrow();
    });
  });
});


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Proprietary widgets
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("in SECTION: Proprietary widgets", function () {
  afterEach(function () {
    jest.restoreAllMocks();
  });
  // swapLoginGate
  describe("swapLoginGate function", function () {
    // A native <dialog>, driven by authmodal.js. jsdom does not implement
    // showModal/close, so they are supplied -- which is also what lets the
    // test assert the dialog was opened rather than inspecting a widget
    // instance that no longer exists.
    function ensureDialog() {
      var dialog = document.getElementById("modalLogin");
      if (!dialog) {
        document.body.insertAdjacentHTML(
          "beforeend", '<dialog id="modalLogin"></dialog>'
        );
        dialog = document.getElementById("modalLogin");
      }
      dialog.showModal = jest.fn(function () { dialog.open = true; });
      dialog.close = jest.fn(function () { dialog.open = false; });
      return dialog;
    }
    function addToggle() {
      document.body.insertAdjacentHTML(
        "beforeend",
        '<a class="id-swap-swap-toggle" href="/swap/ADDR/123/">Swap</a>'
      );
    }
    it("opens the login dialog when an anonymous visitor clicks Swap", function () {
      var dialog = ensureDialog();
      addToggle();
      var event = $.Event("click");
      $(".id-swap-swap-toggle").trigger(event);
      expect(dialog.showModal).toHaveBeenCalled();
      expect(event.isDefaultPrevented()).toBe(true);
    });
    // The page's own hidden field, seeded with a value that is not the answer.
    //
    // These tests used to append a *second* input with this id. That worked
    // while the fixture was a stale snapshot with no such field; now that the
    // fixture is the rendered page, the real one comes first in the document
    // and `getElementById` returns it, so the appended copy was ignored. The
    // empty-href case then asserted "" against a field that was already "" and
    // would have passed with the handler deleted.
    function seedNext(value) {
      var field = document.getElementById("id_modal_login_next");
      field.value = value;
      return field;
    }
    it("records the swap URL on the hidden login field", function () {
      ensureDialog();
      var next = seedNext("stale");
      addToggle();
      $(".id-swap-swap-toggle").trigger($.Event("click"));
      expect(next.value).toBe("/swap/ADDR/123/");
    });
    it("stages an empty next when the Swap link has no href", function () {
      ensureDialog();
      var next = seedNext("stale");
      document.body.insertAdjacentHTML(
        "beforeend", '<a class="id-swap-swap-toggle">Swap</a>'
      );
      $(".id-swap-swap-toggle").trigger($.Event("click"));
      expect(next.value).toBe("");
    });
    it("still opens the dialog when the hidden field is missing", function () {
      // The `if (nextInput)` guard. `modal_login.html` always renders the
      // field, so this is defensive -- but the guard exists precisely because
      // something else could stop rendering it, and an unguarded write would
      // throw before `showModal()` and swallow the whole login affordance.
      //
      // Covered by an explicit removal rather than by the fixture happening to
      // lack the element, which is how it was covered before and is a reason
      // for a test to stop testing anything without failing.
      var dialog = ensureDialog();
      var field = document.getElementById("id_modal_login_next");
      field.parentNode.removeChild(field);
      addToggle();
      var event = $.Event("click");

      expect(function () {
        $(".id-swap-swap-toggle").trigger(event);
      }).not.toThrow();
      expect(dialog.showModal).toHaveBeenCalled();
      expect(event.isDefaultPrevented()).toBe(true);
    });
    it("lets the click navigate for an authenticated visitor", function () {
      // No dialog is rendered for a signed-in user, so the link must be left
      // alone -- swap_source redirects anonymous visitors to login anyway.
      var dialog = document.getElementById("modalLogin");
      if (dialog) dialog.parentNode.removeChild(dialog);
      addToggle();
      var event = $.Event("click");
      $(".id-swap-swap-toggle").trigger(event);
      expect(event.isDefaultPrevented()).toBe(false);
    });
    it("leaves an already-open dialog alone", function () {
      // showModal() on an open <dialog> throws InvalidStateError, which would
      // abort the handler and leave `next` staged but the reader stuck.
      var dialog = ensureDialog();
      dialog.open = true;
      addToggle();

      $(".id-swap-swap-toggle").trigger($.Event("click"));

      expect(dialog.showModal).not.toHaveBeenCalled();
    });

    it("does not double-bind across mainSite calls", function () {
      var dialog = ensureDialog();
      site.mainSite(); // second call must not add a second delegated handler
      addToggle();
      $(".id-swap-swap-toggle").trigger($.Event("click"));
      expect(dialog.showModal).toHaveBeenCalledTimes(1);
    });
  });
  // showSwapErrorToast
  describe("showSwapErrorToast function", function () {
    afterEach(function () {
      window.history.replaceState({}, "", "/");
    });
    // Scoped to the toast's own class rather than `[role="alert"]` alone.
    // The page carries a second, permanent alert -- `#evm-app-error`, hidden
    // until the wallet list needs it -- and it comes first in the document, so
    // the looser selector returned that one and never the toast: the "removes
    // the notice" and "does nothing without swap_error" cases both passed by
    // finding an element the function had not touched. The old fixture
    // predated that div, which is why this only surfaced once the fixture was
    // rendered from the real page.
    function notice() {
      return document.querySelector('.alert-error[role="alert"]');
    }
    it("renders a notice and strips the param when swap_error is present", function () {
      window.history.replaceState({}, "", "/ADDR/?swap_error=unlinked");
      site.showSwapErrorToast();
      expect(notice()).not.toBeNull();
      expect(notice().textContent).toContain("linked to your account");
      expect(window.location.search).toBe("");
    });
    it("uses a generic message for an unknown code", function () {
      window.history.replaceState({}, "", "/ADDR/?swap_error=whatever");
      site.showSwapErrorToast();
      expect(notice().textContent).toBe("Swap is not available.");
    });
    it("removes the notice after a while", function () {
      jest.useFakeTimers();
      window.history.replaceState({}, "", "/ADDR/?swap_error=unlinked");
      site.showSwapErrorToast();
      jest.advanceTimersByTime(6001);
      expect(notice()).toBeNull();
      jest.useRealTimers();
    });
    it("keeps the rest of the query and the hash when stripping the param", function () {
      // The param is removed from a url that may carry others; dropping them
      // too would silently discard state the page was opened with.
      window.history.replaceState({}, "", "/ADDR/?keep=1&swap_error=unlinked#sec");
      site.showSwapErrorToast();

      expect(window.location.search).toBe("?keep=1");
      expect(window.location.hash).toBe("#sec");
      expect(window.location.pathname).toBe("/ADDR/");
    });

    it("does nothing without swap_error", function () {
      window.history.replaceState({}, "", "/ADDR/");
      site.showSwapErrorToast();
      expect(notice()).toBeNull();
    });
  });
});
