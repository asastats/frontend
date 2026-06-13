const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

const subscriptions = require('../static/js/subscriptions.js');

beforeEach(() => {
  document.body.innerHTML = '<input type="checkbox" class="checks" />';
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

  // mainSubscriptions
  describe("mainSubscriptions function", function () {
    it('disables the click on .checks elements', function () {
      subscriptions.mainSubscriptions();
      expect($('.checks').triggerHandler('click')).toBe(false);
    });
  });
});
