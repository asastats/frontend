const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.resolve(__dirname, './index.html'), 'utf8');
const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

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
    it('binds submit and shows stored entries in the app', function () {
      localStorage.setItem("asastats.recentAddresses", JSON.stringify(["a.algo"]));
      $('html').addClass('in-app');
      $("#id_form").off("submit");
      index.mainIndex();
      var events = getEvents($("#id_form")[0]);
      expect(events.submit[0].handler.name).toBe("rememberEntries");
      $('#id_address').trigger('click');
      expect($('#id_address_history .recent-entry').length).toBe(1);
      $('html').removeClass('in-app');
      localStorage.clear();
    });
    it('binds no submit and lists nothing in a browser', function () {
      localStorage.setItem("asastats.recentAddresses", JSON.stringify(["a.algo"]));
      $("#id_form").off("submit");
      index.mainIndex();
      var events = getEvents($("#id_form")[0]);
      expect(events && events.submit).toBe(undefined);
      expect($('#id_address_history').length).toBe(0);
      localStorage.clear();
    });
    it('binds click on track button', function () {
      $("#track").off("click");
      index.mainIndex()
      var events = getEvents($("#track")[0]);
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

  const ADDRESS = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU";
  const OTHER = "2UEQTE5QDNXPI7M3TU44G6SYKLFWLPQO7EBZM7K7MHMQQMFI4QJPLHQFHM";

  // isRememberable
  describe("isRememberable function", function () {
    it('accepts an Algorand address and .algo names', function () {
      expect(index.isRememberable(ADDRESS)).toBe(true);
      expect(index.isRememberable("asastats.algo")).toBe(true);
      expect(index.isRememberable("Sub.Name.algo/nfd")).toBe(true);
      expect(index.isRememberable("name.algo/ans")).toBe(true);
    });
    it('rejects anything else', function () {
      expect(index.isRememberable(ADDRESS.toLowerCase())).toBe(false);
      expect(index.isRememberable(ADDRESS.slice(1))).toBe(false);
      expect(index.isRememberable("name.algo/xyz")).toBe(false);
      expect(index.isRememberable("<b>.algo")).toBe(false);
      expect(index.isRememberable("")).toBe(false);
      expect(index.isRememberable(42)).toBe(false);
    });
  });

  // recentEntries
  describe("recentEntries function", function () {
    beforeEach(() => localStorage.clear());
    it('returns an empty array when nothing is stored', function () {
      expect(index.recentEntries()).toEqual([]);
    });
    it('returns stored entries without invalid ones', function () {
      localStorage.setItem("asastats.recentAddresses",
        JSON.stringify([ADDRESS, "junk", 7, "a.algo"]));
      expect(index.recentEntries()).toEqual([ADDRESS, "a.algo"]);
    });
    it('returns an empty array for a stored non-array', function () {
      localStorage.setItem("asastats.recentAddresses", JSON.stringify({a: 1}));
      expect(index.recentEntries()).toEqual([]);
    });
    it('returns an empty array for unparsable storage', function () {
      localStorage.setItem("asastats.recentAddresses", "{");
      expect(index.recentEntries()).toEqual([]);
    });
  });

  // rememberEntries
  describe("rememberEntries function", function () {
    beforeEach(() => localStorage.clear());
    const stored = () => JSON.parse(localStorage.getItem("asastats.recentAddresses"));
    it('stores the input value first and drops duplicates', function () {
      localStorage.setItem("asastats.recentAddresses", JSON.stringify([OTHER, ADDRESS]));
      $('#id_address').val(ADDRESS);
      index.rememberEntries();
      expect(stored()).toEqual([ADDRESS, OTHER]);
    });
    it('stores every valid entry from the textarea', function () {
      $('#id_address').replaceWith('<textarea id="id_addresses"></textarea>');
      $('#id_addresses').val(ADDRESS + ",\n bad " + OTHER + " x.algo");
      index.rememberEntries();
      expect(stored()).toEqual([ADDRESS, OTHER, "x.algo"]);
    });
    it('stores nothing for invalid input', function () {
      $('#id_address').val("not an address");
      index.rememberEntries();
      expect(localStorage.getItem("asastats.recentAddresses")).toBe(null);
    });
    it('stores nothing for an empty input', function () {
      $('#id_address').remove();
      index.rememberEntries();
      expect(localStorage.getItem("asastats.recentAddresses")).toBe(null);
    });
    it('keeps at most twenty entries', function () {
      const names = Array.from({length: 25}, (_, i) => "n" + i + ".algo");
      localStorage.setItem("asastats.recentAddresses", JSON.stringify(names));
      $('#id_address').val(ADDRESS);
      index.rememberEntries();
      expect(stored().length).toBe(20);
      expect(stored()[0]).toBe(ADDRESS);
      expect(stored()[19]).toBe("n18.algo");
    });
    it('ignores a storage failure', function () {
      localStorage.setItem.mockImplementationOnce(() => {
        throw new Error("full");
      });
      $('#id_address').val(ADDRESS);
      expect(() => index.rememberEntries()).not.toThrow();
      expect(localStorage.getItem("asastats.recentAddresses")).toBe(null);
    });
  });

  // showRecentEntries and the suggestion list
  describe("suggestion list", function () {
    const KEY = "asastats.recentAddresses";
    const rows = () => $('#id_address_history .recent-entry').map(function () {
      return $(this).attr('data-entry');
    }).get();
    beforeEach(() => {
      localStorage.clear();
      localStorage.setItem(KEY, JSON.stringify([OTHER, ADDRESS, "abc.algo"]));
      index.showRecentEntries();
    });

    it('builds one hidden list beside the input', function () {
      index.showRecentEntries();
      expect($('#id_address_history').length).toBe(1);
      expect($('#id_address_history').hasClass('hidden')).toBe(true);
      expect($('#id_address').parent().hasClass('relative')).toBe(true);
      expect($('#id_address_history').parent()[0]).toBe($('#id_address').parent()[0]);
    });
    it('shows every stored entry in order on focus', function () {
      $('#id_address').trigger('focus');
      expect($('#id_address_history').hasClass('hidden')).toBe(false);
      expect(rows()).toEqual([OTHER, ADDRESS, "abc.algo"]);
    });
    it('filters by what is typed, ignoring case', function () {
      $('#id_address').val("ABC").trigger('input');
      expect(rows()).toEqual(["abc.algo"]);
    });
    it('hides when nothing matches', function () {
      $('#id_address').val("zzz").trigger('input');
      expect(rows()).toEqual([]);
      expect($('#id_address_history').hasClass('hidden')).toBe(true);
    });
    it('hides when nothing is stored', function () {
      localStorage.clear();
      $('#id_address').trigger('click');
      expect($('#id_address_history').hasClass('hidden')).toBe(true);
    });
    it('hides when the input has been replaced', function () {
      $('#id_address').remove();
      index.renderRecentEntries();
      expect($('#id_address_history').hasClass('hidden')).toBe(true);
    });
    it('hides on blur and on Escape but not on other keys', function () {
      $('#id_address').trigger('focus').trigger('blur');
      expect($('#id_address_history').hasClass('hidden')).toBe(true);
      $('#id_address').trigger('click');
      $('#id_address').trigger($.Event('keydown', {key: 'a'}));
      expect($('#id_address_history').hasClass('hidden')).toBe(false);
      $('#id_address').trigger($.Event('keydown', {key: 'Escape'}));
      expect($('#id_address_history').hasClass('hidden')).toBe(true);
    });
    it('hides when switching to the textarea', function () {
      $('#id_address').trigger('click');
      $('.prefix').trigger('click');
      expect($('#id_address_history').hasClass('hidden')).toBe(true);
    });
    it('keeps focus on the input when a row is pressed', function () {
      const event = $.Event('mousedown');
      $('#id_address_history').trigger(event);
      expect(event.isDefaultPrevented()).toBe(true);
    });
    it('fills the input with a chosen entry', function () {
      $('#id_address').trigger('click');
      $('#id_address_history .recent-entry').eq(1).trigger('click');
      expect($('#id_address').val()).toBe(ADDRESS);
      expect($('#id_address_history').hasClass('hidden')).toBe(true);
    });
    it('forgets an entry and keeps the others listed', function () {
      $('#id_address').trigger('click');
      $('#id_address_history .recent-forget').eq(0).trigger('click');
      expect(JSON.parse(localStorage.getItem(KEY))).toEqual([ADDRESS, "abc.algo"]);
      expect(rows()).toEqual([ADDRESS, "abc.algo"]);
      expect($('#id_address').val()).toBe("");
    });
    it('names the entry on its forget button', function () {
      $('#id_address').trigger('click');
      expect($('#id_address_history .recent-forget').eq(2).attr('aria-label')).toBe("Forget abc.algo");
    });
    it('ignores a click between rows', function () {
      $('#id_address').trigger('click');
      $('#id_address_history').trigger('click');
      expect($('#id_address_history').hasClass('hidden')).toBe(false);
    });
    it('ignores a storage failure when forgetting', function () {
      localStorage.setItem.mockImplementationOnce(() => { throw new Error("full"); });
      expect(() => index.forgetEntry(OTHER)).not.toThrow();
      expect(JSON.parse(localStorage.getItem(KEY)).length).toBe(3);
    });
    it('writes entries as text, never as markup', function () {
      localStorage.setItem(KEY, JSON.stringify(["a-b.algo"]));
      $('#id_address').trigger('click');
      expect($('#id_address_history .recent-entry').html()).toBe("a-b.algo");
    });
  });

  // removeError
  // setDefault
  // setProgress

});
