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
    function addToggle() {
      document.body.insertAdjacentHTML(
        "beforeend",
        '<a class="id-swap-swap-toggle" href="/swap/source/">Swap</a>'
      );
    }
    it("opens the login modal when an anonymous visitor clicks Swap", function () {
      // #modalLogin is rendered only for anonymous users; ensure it is present.
      if (!document.getElementById("modalLogin")) {
        document.body.insertAdjacentHTML(
          "beforeend",
          '<div id="modalLogin" class="modal"></div>'
        );
      }
      var openSpy = jest.fn();
      jest
        .spyOn(M.Modal, "getInstance")
        .mockReturnValue({ open: openSpy, options: {} });
      addToggle();
      var event = $.Event("click");
      $(".id-swap-swap-toggle").trigger(event);
      expect(openSpy).toHaveBeenCalled();
      expect(event.isDefaultPrevented()).toBe(true);
    });
    it("ignores a Swap click for an authenticated visitor (no modal)", function () {
      var modalEl = document.getElementById("modalLogin");
      if (modalEl) {
        modalEl.parentNode.removeChild(modalEl);
      }
      var openSpy = jest.fn();
      jest
        .spyOn(M.Modal, "getInstance")
        .mockReturnValue({ open: openSpy, options: {} });
      addToggle();
      var event = $.Event("click");
      $(".id-swap-swap-toggle").trigger(event);
      expect(openSpy).not.toHaveBeenCalled();
      expect(event.isDefaultPrevented()).toBe(false);
    });
    it("does not double-bind across mainSite calls", function () {
      if (!document.getElementById("modalLogin")) {
        document.body.insertAdjacentHTML(
          "beforeend",
          '<div id="modalLogin" class="modal"></div>'
        );
      }
      var openSpy = jest.fn();
      jest
        .spyOn(M.Modal, "getInstance")
        .mockReturnValue({ open: openSpy, options: {} });
      site.mainSite(); // second call must not add a second delegated handler
      addToggle();
      $(".id-swap-swap-toggle").trigger($.Event("click"));
      expect(openSpy).toHaveBeenCalledTimes(1);
    });
  });
});
