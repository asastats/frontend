const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.resolve(__dirname, './index.html'), 'utf8');
const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

const materialize = require('../static/js/materialize.min.js');
const index = require('../static/js/index.js');

jest
  .dontMock('fs');

beforeEach(() => {
  document.documentElement.innerHTML = html.toString();
  index.mainIndex();
});

afterEach(() => {
  jest.resetModules();
});


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Initialization
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("in SECTION: Initialization", function () {

  // mainIndex
  describe("mainIndex function", function () {
    it('binds pageshow event on window', function () {
      $(window).off("pageshow");
      index.mainIndex()
      var events = getEvents($(window)[0]);
      expect(events).not.toBe(undefined);
      expect(events.pageshow[0].handler.name).toBe("setDefault");
    });
    it('binds change paste keyup click on address input', function () {
      $("#id_address").off("change paste keyup click");
      index.mainIndex()
      var events = getEvents($("#id_address")[0]);
      expect(events).not.toBe(undefined);
      expect(events.change[0].handler.name).toBe("removeError");
    });
    it('binds click on whenmoon button', function () {
      $("#whenmoon").off("click");
      index.mainIndex()
      var events = getEvents($("#whenmoon")[0]);
      expect(events).not.toBe(undefined);
      expect(events.click[0].handler.name).toBe("setProgress");
    });
  });
});


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("in SECTION: Helper functions", function () {

  // removeError
  // setDefault
  // setProgress

});
