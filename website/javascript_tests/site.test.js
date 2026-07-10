const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.resolve(__dirname, './index.html'), 'utf8');
const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

$.prototype.sidenav = jest.fn();
$.prototype.modal = jest.fn();

const materialize = require('../static/js/materialize.min.js');
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
  describe("share button exist", function () {
    it('for X/Twitter', function () {
      const href = $(".scbtn.twitbtn").attr('href');
      expect(href).toEqual(expect.stringContaining("x.com"));
    });
    it('for LinkedIn', function () {
      const href = $(".scbtn.dscrbtn").attr('href');
      expect(href).toEqual(expect.stringContaining("discord.gg"));
    });
    it('for Reddit', function () {
      const href = $(".scbtn.rdtbtn").attr('href');
      expect(href).toEqual(expect.stringContaining("reddit.com"));
    });
  });
  describe("other buttons exist", function () {
    it('for dark/bright mode', function () {
      const href = $(".scbtn.brightbtn").attr('href');
      expect(href).toEqual("#");
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
    it('initializes sidenav', function () {
      const spyFunc = jest.spyOn($.prototype, "sidenav");
      spyFunc.mockClear();
      const index = require('../static/js/site.js');
      index.mainSite();
      expect(spyFunc).toHaveBeenCalledWith();
    });
    it('checks localStorage', function () {
      const spyFunc = jest.spyOn(localStorage, "getItem");
      spyFunc.mockClear();
      site.mainSite();
      expect(spyFunc).toHaveBeenCalled();
    });
    it('binds click event on dark/bright toggle button', function () {
      $(".dark-toggle").off("click");
      site.mainSite();
      var events = getEvents($(".dark-toggle")[0]);
      expect(events).not.toBe(undefined);
      expect(events.click[0].handler.name).toBe("toggleMode");
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
    function ensureModal() {
      if (!document.getElementById("modalLogin")) {
        document.body.insertAdjacentHTML(
          "beforeend",
          '<div id="modalLogin" class="modal"></div>'
        );
      }
    }
    function addToggle() {
      document.body.insertAdjacentHTML(
        "beforeend",
        '<a class="id-swap-swap-toggle" href="/swap/ADDR/123/">Swap</a>'
      );
    }
    it("opens the login modal when an anonymous visitor clicks Swap", function () {
      ensureModal();
      var openSpy = jest.fn();
      jest.spyOn(M.Modal, "getInstance").mockReturnValue({ open: openSpy });
      addToggle();
      var event = $.Event("click");
      $(".id-swap-swap-toggle").trigger(event);
      expect(openSpy).toHaveBeenCalled();
      expect(event.isDefaultPrevented()).toBe(true);
    });
    it("carries the swap URL into the email field and wallet data-next", function () {
      ensureModal();
      document.body.insertAdjacentHTML(
        "beforeend",
        '<input id="id_modal_login_next" name="next" value="" />' +
          '<div id="wallet-connect"></div>'
      );
      jest.spyOn(M.Modal, "getInstance").mockReturnValue({ open: jest.fn() });
      addToggle();
      $(".id-swap-swap-toggle").trigger($.Event("click"));
      expect(document.getElementById("id_modal_login_next").value).toBe(
        "/swap/ADDR/123/"
      );
      expect(document.getElementById("wallet-connect").dataset.next).toBe(
        "/swap/ADDR/123/"
      );
    });
    it("stages an empty next when the Swap link has no href", function () {
      ensureModal();
      document.body.insertAdjacentHTML(
        "beforeend",
        '<input id="id_modal_login_next" name="next" value="stale" />' +
          '<div id="wallet-connect" data-next="stale"></div>'
      );
      jest.spyOn(M.Modal, "getInstance").mockReturnValue({ open: jest.fn() });
      document.body.insertAdjacentHTML(
        "beforeend",
        '<a class="id-swap-swap-toggle">Swap</a>'
      );
      $(".id-swap-swap-toggle").trigger($.Event("click"));
      expect(document.getElementById("id_modal_login_next").value).toBe("");
      expect(document.getElementById("wallet-connect").dataset.next).toBe("");
    });
    it("ignores a Swap click for an authenticated visitor (no modal)", function () {
      var modalEl = document.getElementById("modalLogin");
      if (modalEl) {
        modalEl.parentNode.removeChild(modalEl);
      }
      var getInstance = jest.spyOn(M.Modal, "getInstance");
      addToggle();
      var event = $.Event("click");
      $(".id-swap-swap-toggle").trigger(event);
      expect(getInstance).not.toHaveBeenCalled();
      expect(event.isDefaultPrevented()).toBe(false);
    });
    it("does not double-bind across mainSite calls", function () {
      ensureModal();
      var openSpy = jest.fn();
      jest.spyOn(M.Modal, "getInstance").mockReturnValue({ open: openSpy });
      site.mainSite(); // second call must not add a second delegated handler
      addToggle();
      $(".id-swap-swap-toggle").trigger($.Event("click"));
      expect(openSpy).toHaveBeenCalledTimes(1);
    });
  });
  // showSwapErrorToast
  describe("showSwapErrorToast function", function () {
    afterEach(function () {
      window.history.replaceState({}, "", "/");
    });
    it("fires a toast and strips the param when swap_error is present", function () {
      window.history.replaceState({}, "", "/ADDR/?swap_error=unlinked");
      var toastSpy = jest.spyOn(M, "toast").mockImplementation(function () {});
      site.showSwapErrorToast();
      expect(toastSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          html: expect.stringContaining("linked to your account"),
        })
      );
      expect(window.location.search).toBe("");
    });
    it("uses a generic message for an unknown code", function () {
      window.history.replaceState({}, "", "/ADDR/?swap_error=whatever");
      var toastSpy = jest.spyOn(M, "toast").mockImplementation(function () {});
      site.showSwapErrorToast();
      expect(toastSpy).toHaveBeenCalledWith(
        expect.objectContaining({ html: "Swap is not available." })
      );
    });
    it("does nothing without swap_error", function () {
      window.history.replaceState({}, "", "/ADDR/");
      var toastSpy = jest.spyOn(M, "toast").mockImplementation(function () {});
      site.showSwapErrorToast();
      expect(toastSpy).not.toHaveBeenCalled();
    });
    it("strips the param and does not throw when M.toast is unavailable", function () {
      window.history.replaceState({}, "", "/ADDR/?swap_error=unlinked");
      var original = M.toast;
      M.toast = undefined;
      try {
        expect(function () {
          site.showSwapErrorToast();
        }).not.toThrow();
        expect(window.location.search).toBe("");
      } finally {
        M.toast = original;
      }
    });
    it("keeps other query params while stripping swap_error", function () {
      window.history.replaceState({}, "", "/ADDR/?swap_error=unlinked&x=1");
      jest.spyOn(M, "toast").mockImplementation(function () {});
      site.showSwapErrorToast();
      expect(window.location.search).toBe("?x=1");
    });
  });
});
