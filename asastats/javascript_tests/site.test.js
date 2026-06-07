const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.resolve(__dirname, './index.html'), 'utf8');
const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

$.prototype.sidenav = jest.fn();

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
    it('for Twitter', function () {
      const href = $(".scbtn.twitbtn").attr('href');
      expect(href).toEqual(expect.stringContaining("twitter.com"));
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
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("in SECTION: Helper functions", function () {

  // checkMode
  // toggleMode
  // toggleText

});
