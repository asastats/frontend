const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

$.prototype.tooltip = jest.fn();

const tax = require('../static/js/tax.js');

const fixture =
  '<form id="process_form"><button id="process"></button></form>' +
  '<button id="download"></button>' +
  '<button id="refresh"></button>' +
  '<a id="back" class="disabled"></a>' +
  '<div class="progress"><div class="indeterminate"></div></div>' +
  '<ul class="errorlist"><li>err</li></ul>';

beforeEach(() => {
  document.body.innerHTML = fixture;
  jest.useFakeTimers();
  tax.mainTax();
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
  jest.resetModules();
});


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Initialization
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("in SECTION: Initialization", function () {

  // mainTax
  describe("mainTax function", function () {
    it('initializes no tooltip plugin', function () {
      // The hints were Materialize tooltips, initialised here. They are CSS
      // now -- `data-tip` on the label -- so there is nothing to construct,
      // and calling a plugin that left with the framework would throw inside
      // jQuery's ready queue and abandon the three bindings after it.
      var spyFunc = jest.spyOn($.prototype, "tooltip");
      spyFunc.mockClear();

      tax.mainTax();

      expect(spyFunc).not.toHaveBeenCalled();
    });
    it('binds pageshow event on window', function () {
      $(window).off("pageshow");
      tax.mainTax();
      var events = getEvents($(window)[0]);
      expect(events.pageshow[0].handler.name).toBe("setDefault");
    });
    it('binds click on download, back and submit on process form', function () {
      $("#download").off("click");
      $("#back").off("click");
      $("#process_form").off("submit");
      tax.mainTax();
      expect(getEvents($("#download")[0]).click[0].handler.name)
        .toBe("removeError");
      expect(getEvents($("#back")[0]).click[0].handler.name)
        .toBe("setProgress");
      expect(getEvents($("#process_form")[0]).submit[0].handler.name)
        .toBe("disableProcessSubmit");
    });

    // There is no plugin call left to guard -- the hints are CSS tooltips --
    // but the shape of the old failure is worth keeping a test for: anything
    // reintroduced here runs inside jQuery's ready queue, ahead of the three
    // bindings below it, and a throw would take them and every later ready
    // callback on the page with it.
    describe('without Materialize, as on the DaisyUI base', function () {
      var tooltip;

      beforeEach(function () {
        tooltip = $.fn.tooltip;
        delete $.fn.tooltip;
      });

      afterEach(function () {
        $.fn.tooltip = tooltip;
      });

      it('does not throw', function () {
        expect(function () { tax.mainTax(); }).not.toThrow();
      });

      it('still binds everything declared after the tooltip call', function () {
        $("#download").off("click");
        $("#back").off("click");
        $("#process_form").off("submit");
        tax.mainTax();
        expect(getEvents($("#download")[0]).click[0].handler.name)
          .toBe("removeError");
        expect(getEvents($("#back")[0]).click[0].handler.name)
          .toBe("setProgress");
        expect(getEvents($("#process_form")[0]).submit[0].handler.name)
          .toBe("disableProcessSubmit");
      });
    });
  });
});


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("in SECTION: Helper functions", function () {

  // setDefault
  describe("setDefault function", function () {
    it('removes progress and re-enables controls on pageshow', function () {
      $('#process').prop("disabled", true);
      $('#back').addClass("disabled");
      $(window).trigger('pageshow');
      expect($('.indeterminate').parent().hasClass('progress')).toBe(false);
      expect($('#process').prop("disabled")).toBe(false);
      expect($('#download').prop("disabled")).toBe(false);
      expect($('#refresh').prop("disabled")).toBe(false);
      expect($('#back').hasClass("disabled")).toBe(false);
      expect(document.body.style.cursor).toBe("default");
    });
  });

  // setProgress
  describe("setProgress function", function () {
    it('adds progress, removes errors and disables controls', function () {
      $("#back").trigger('click');
      expect($('.indeterminate').parent().hasClass('progress')).toBe(true);
      expect(document.body.style.cursor).toBe("progress");
      expect($('.errorlist').length).toBe(0);
      jest.runOnlyPendingTimers();
      expect($('#back').hasClass('disabled')).toBe(true);
      expect($('#download').attr('disabled')).toBe('disabled');
      expect($('#refresh').attr('disabled')).toBe('disabled');
    });
  });

  // removeError
  describe("removeError function", function () {
    it('removes the error list from the page', function () {
      $("#download").trigger('click');
      expect($('.errorlist').length).toBe(0);
    });
  });

  // disableProcessSubmit
  describe("disableProcessSubmit function", function () {
    it('disables the process button after submit', function () {
      $("#process_form").trigger('submit');
      jest.runOnlyPendingTimers();
      expect($('#process').attr('disabled')).toBe('disabled');
    });
  });
});
