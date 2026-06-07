const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.resolve(__dirname, './address.html'), 'utf8');
const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;
// window.Chart = require('../static/js/chart.min.js');

$.prototype.collapsible = jest.fn();
$.prototype.tooltip = jest.fn();
window.Chart = jest.fn();
// window.canvas = jest.fn();

const materialize = require('../static/js/materialize.min.js');
const chart = require('../static/js/chart.min.js');
const address = require('../static/js/address.js');

jest
  .dontMock('fs');

beforeEach(() => {
  document.documentElement.innerHTML = html.toString();
  address.mainAddress();
});

afterEach(() => {
  jest.resetModules();
});


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Initialization
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
// describe("in SECTION: Initialization", function () {

//   mainAddress
//   describe("mainAddress function", function () {
//     it('initializes collapsible', function () {
//       const spyFunc = jest.spyOn($.prototype, "collapsible");
//       spyFunc.mockClear();
//       const address = require('../static/js/address.js');
//       address.mainAddress();
//       expect(spyFunc).toHaveBeenCalledWith();
//     });
//     it('initializes tooltip', function () {
//       const spyFunc = jest.spyOn($.prototype, "tooltip");
//       spyFunc.mockClear();
//       const address = require('../static/js/address.js');
//       address.mainAddress();
//       expect(spyFunc).toHaveBeenCalledWith();
//     });

//   });
// });


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("in SECTION: Helper functions", function () {

  // isNotVisible
  // parseJsonScript
  // populateCharts
  // scrollToView

});
