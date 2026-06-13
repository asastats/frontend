const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

global.M = { textareaAutoResize: jest.fn() };

const index = require('../static/js/index.js');

const fixture =
  '<input id="id_address" value="">' +
  '<span class="prefix"></span>' +
  '<a class="ns" id="algo"></a>' +
  '<input type="hidden" id="id_bundle">' +
  '<div class="progress"><div class="indeterminate"></div></div>' +
  '<button id="whenmoon"></button>' +
  '<ul class="errorlist"><li>err</li></ul>';

beforeEach(() => {
  document.body.innerHTML = fixture;
  jest.useFakeTimers();
  index.mainIndex();
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
  jest.resetModules();
});


describe("in SECTION: Helper functions", function () {

  // addNS
  describe("addNS function", function () {
    it('appends the name service suffix to a plain address', function () {
      $("#id_address").val("MYADDRESS");
      $(".ns").trigger("click");
      expect($("#id_address").val()).toBe("MYADDRESS/algo");
    });
    it('replaces an existing /ans suffix', function () {
      $("#id_address").val("MYADDRESS/ans");
      $(".ns").trigger("click");
      expect($("#id_address").val()).toBe("MYADDRESS/algo");
    });
    it('replaces an existing /nfd suffix', function () {
      $("#id_address").val("MYADDRESS/nfd");
      $(".ns").trigger("click");
      expect($("#id_address").val()).toBe("MYADDRESS/algo");
    });
  });

  // removeError
  describe("removeError function", function () {
    it('removes the error list from the page', function () {
      index.removeError(null);
      expect($('.errorlist').length).toBe(0);
    });
  });

  // setDefault
  describe("setDefault function", function () {
    it('removes progress and re-enables the moon button', function () {
      $('#whenmoon').prop("disabled", true);
      index.setDefault(null);
      expect($('.indeterminate').parent().hasClass('progress')).toBe(false);
      expect($('#whenmoon').prop("disabled")).toBe(false);
      expect(document.body.style.cursor).toBe("default");
    });
  });

  // setProgress
  describe("setProgress function", function () {
    it('adds progress, removes errors and disables the moon button', function () {
      index.setProgress(null);
      expect($('.indeterminate').parent().hasClass('progress')).toBe(true);
      expect(document.body.style.cursor).toBe("progress");
      expect($('.errorlist').length).toBe(0);
      jest.runOnlyPendingTimers();
      expect($('#whenmoon').attr('disabled')).toBe('disabled');
    });
  });

  // replaceTextarea / createTextarea / updateBundle
  describe("replaceTextarea function", function () {
    it('replaces the input with a textarea and updates the bundle', function () {
      $("#id_address").val("ADDR-ONE");
      $(".prefix").trigger("click");
      expect($("#id_addresses").length).toBe(1);
      expect($("#id_addresses").val()).toBe("ADDR-ONE");
      expect($("#id_bundle").val()).toBe("ADDR-ONE");
      expect(M.textareaAutoResize).toHaveBeenCalled();
    });
    it('updates the bundle when the textarea changes', function () {
      $("#id_address").val("ADDR-ONE");
      $(".prefix").trigger("click");
      $("#id_addresses").val("ADDR-TWO");
      $("#id_addresses").trigger("change");
      expect($("#id_bundle").val()).toBe("ADDR-TWO");
    });
  });

  // setTextarea
  describe("setTextarea function", function () {
    var longValue = "A".repeat(58);

    it('replaces the input on space once the address is long enough', function () {
      $("#id_address").val(longValue);
      var input = $("#id_address")[0];
      index.setTextarea.call(input, { keyCode: 32 });
      expect($("#id_addresses").length).toBe(1);
    });
    it('does nothing when the key is not space', function () {
      $("#id_address").val(longValue);
      var input = $("#id_address")[0];
      index.setTextarea.call(input, { keyCode: 13 });
      expect($("#id_addresses").length).toBe(0);
    });
    it('does nothing when the address is too short', function () {
      $("#id_address").val("short");
      var input = $("#id_address")[0];
      index.setTextarea.call(input, { keyCode: 32 });
      expect($("#id_addresses").length).toBe(0);
    });
  });

  // updateBundle
  describe("updateBundle function", function () {
    it('copies the textarea value into the hidden bundle field', function () {
      $("#id_address").replaceWith(
        '<textarea id="id_addresses">BUNDLE-VAL</textarea>'
      );
      index.updateBundle();
      expect($("#id_bundle").val()).toBe("BUNDLE-VAL");
    });
  });
});
