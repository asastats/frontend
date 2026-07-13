const jquery = require("../static/js/jquery-2.2.4.min.js");

window.$ = jquery;

$.prototype.sidenav = jest.fn();
$.prototype.modal = jest.fn();

const site = require("../static/js/site.js");

const fixture =
  '<div class="sidenav"></div><div class="modal"></div>' +
  '<div id="footer" data-mode="light"></div>' +
  '<img id="logo"><img id="brand"><span id="cpr"></span>' +
  '<a class="dark-toggle"></a><span class="txt"></span>' +
  '<span class="thelink">copy me</span><a class="copy"></a>';

beforeEach(() => {
  document.body.innerHTML = fixture;
  localStorage.clear();
  jest.useFakeTimers();
  site.mainSite();
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
  jest.resetModules();
});

describe("in SECTION: Helper functions", function () {
  // mainSite dark branch (covers the toggleText call on init)
  describe("mainSite in dark mode", function () {
    it("toggles text when the saved mode is dark", function () {
      localStorage.setItem("mode", "dark");
      site.mainSite();
      expect($("html").hasClass("dark")).toBe(true);
      expect($(".dark-toggle").attr("class")).toContain("darkbtn");
    });
  });

  // checkMode / isDark
  describe("checkMode function", function () {
    it("applies dark assets when footer data-mode is dark", function () {
      $("#footer").attr("data-mode", "dark");
      site.checkMode();
      expect($("html").hasClass("dark")).toBe(true);
      expect($("#logo").attr("src")).toContain("logo-dark.png");
      expect($("#brand").attr("src")).toContain("asastats-dark.png");
      expect($("#cpr").hasClass("mydark-text")).toBe(true);
    });

    it("applies dark assets when localStorage mode is dark", function () {
      localStorage.setItem("mode", "dark");
      site.checkMode();
      expect($("html").hasClass("dark")).toBe(true);
    });

    it("applies bright assets otherwise", function () {
      $("#footer").attr("data-mode", "light");
      site.checkMode();
      expect($("html").hasClass("dark")).toBe(false);
      expect($("#logo").attr("src")).toContain("logo.png");
      expect($("#brand").attr("src")).toContain("asastats.png");
    });
  });

  // toggleMode
  describe("toggleMode function", function () {
    it("switches mode from light to dark", function () {
      localStorage.setItem("mode", "light");
      site.toggleMode(null);
      expect(localStorage.getItem("mode")).toBe("dark");
    });
    it("switches mode from dark to light", function () {
      localStorage.setItem("mode", "dark");
      site.toggleMode(null);
      expect(localStorage.getItem("mode")).toBe("light");
    });
    it("defaults missing mode to dark", function () {
      site.toggleMode(null);
      expect(localStorage.getItem("mode")).toBe("dark");
    });
  });

  // toggleText
  describe("toggleText function", function () {
    it("toggles the dark toggle and text classes", function () {
      site.toggleText();
      expect($(".dark-toggle").hasClass("brightbtn")).toBe(true);
      expect($(".txt").hasClass("myredlight-text")).toBe(true);
    });
  });

  // copyToClipboard
  describe("copyToClipboard function", function () {
    it("writes the previous element text to the clipboard", function () {
      var writeText = jest.fn();
      Object.defineProperty(global.navigator, "clipboard", {
        value: { writeText: writeText },
        configurable: true,
      });
      $(".thelink").css("color", "rgb(1, 2, 3)");
      $(".copy").trigger("click");
      expect(writeText).toHaveBeenCalledWith("copy me");
      expect($(".thelink").css("color")).not.toBe("rgb(1, 2, 3)");
      jest.runOnlyPendingTimers();
      expect($(".thelink").css("color")).toBe("rgb(1, 2, 3)");
    });
    it("does nothing when clipboard is unavailable", function () {
      Object.defineProperty(global.navigator, "clipboard", {
        value: undefined,
        configurable: true,
      });
      $(".thelink").css("color", "rgb(1, 2, 3)");
      $(".copy").trigger("click");
      expect($(".thelink").css("color")).toBe("rgb(1, 2, 3)");
    });
  });
});

/*
 * initializeCookieConsent is NOT exported and is commented out in mainSite,
 * so it is unreachable from tests as shipped. Add it to site.js module.exports
 * and this block activates automatically (otherwise it is skipped).
 */
var hasCookieConsent = typeof site.initializeCookieConsent === "function";
var describeCookie = hasCookieConsent ? describe : describe.skip;
describeCookie("initializeCookieConsent function", function () {
  it("configures the cookie banner and wires the callbacks", function () {
    global.gtag = jest.fn();
    global.dataLayer = { push: jest.fn() };
    global.silktideCookieBannerManager = {
      updateCookieBannerConfig: jest.fn(),
    };
    var logSpy = jest.spyOn(console, "log").mockImplementation(function () {});
    site.initializeCookieConsent();
    var config =
      global.silktideCookieBannerManager.updateCookieBannerConfig.mock
        .calls[0][0];
    config.cookieTypes[0].onAccept();
    config.cookieTypes[1].onAccept();
    config.cookieTypes[1].onReject();
    config.cookieTypes[2].onAccept();
    config.cookieTypes[2].onReject();
    expect(
      global.silktideCookieBannerManager.updateCookieBannerConfig,
    ).toHaveBeenCalled();
    expect(global.gtag).toHaveBeenCalled();
    expect(global.dataLayer.push).toHaveBeenCalled();
    expect(logSpy).toHaveBeenCalled();
    logSpy.mockRestore();
  });
});
