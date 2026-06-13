const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

const home = require('../static/js/home.js');

const fixture =
  '<input type="radio" name="sort" id="id_name">' +
  '<input type="checkbox" id="id_desc">' +
  '<input type="text" id="id_filter">' +
  '<div class="bundlenames">' +
  '<div data-name="b">B</div><div data-name="a">A</div>' +
  '</div>' +
  '<div class="cardiv" data-name="alpha" data-addresses="addr1"' +
  ' data-created="2020" data-modified="2021"><div><div title="Alpha">' +
  '</div></div></div>' +
  '<div class="cardiv" data-name="beta" data-addresses="addr2"' +
  ' data-created="2022" data-modified="2023"><div><div title="Beta">' +
  '</div></div></div>';

beforeEach(() => {
  document.body.innerHTML = fixture;
  home.mainHome();
});

afterEach(() => {
  jest.resetModules();
});


describe("in SECTION: Initialization", function () {

  describe("mainHome function", function () {
    it('binds change on sort radios, descending and filter inputs', function () {
      $("input[type=radio][name=sort]").off("change");
      $("#id_desc").off("change");
      $("#id_filter").off("change paste keyup");
      home.mainHome();
      expect(getEvents($("input[type=radio][name=sort]")[0]).change[0]
        .handler.name).toBe("changeSorting");
      expect(getEvents($("#id_desc")[0]).change[0].handler.name)
        .toBe("changeDescending");
      expect(getEvents($("#id_filter")[0]).change[0].handler.name)
        .toBe("changeFiltering");
    });
  });
});


describe("in SECTION: Panel input events", function () {

  describe("changeDescending function", function () {
    it('reverses the order of the bundlename cards', function () {
      home.changeDescending(null);
      var order = $(".bundlenames > div").map(function () {
        return $(this).data("name");
      }).get();
      expect(order).toEqual(["a", "b"]);
    });
  });

  describe("changeSorting function", function () {
    it('sorts ascending when descending is unchecked', function () {
      var radio = $("#id_name")[0];
      home.changeSorting.call(radio, null);
      var order = $(".bundlenames > div").map(function () {
        return $(this).data("name");
      }).get();
      expect(order).toEqual(["a", "b"]);
    });
    it('sorts descending when descending is checked', function () {
      $("#id_desc").prop("checked", true);
      var radio = $("#id_name")[0];
      home.changeSorting.call(radio, null);
      var order = $(".bundlenames > div").map(function () {
        return $(this).data("name");
      }).get();
      expect(order).toEqual(["b", "a"]);
    });
    it('keeps already-ascending order (covers comparator else)', function () {
      $(".bundlenames").html(
        '<div data-name="a">A</div><div data-name="b">B</div>'
      );
      var radio = $("#id_name")[0];
      home.changeSorting.call(radio, null);
      var order = $(".bundlenames > div").map(function () {
        return $(this).data("name");
      }).get();
      expect(order).toEqual(["a", "b"]);
    });
  });

  describe("changeFiltering function", function () {
    it('shows all cards when the filter is empty', function () {
      $("#id_filter").val("");
      home.changeFiltering(null);
      expect($(".cardiv").eq(0).css("display")).not.toBe("none");
      expect($(".cardiv").eq(1).css("display")).not.toBe("none");
    });
    it('shows only cards matching the title', function () {
      $("#id_filter").val("alpha");
      home.changeFiltering(null);
      expect($(".cardiv").eq(0).css("display")).not.toBe("none");
      expect($(".cardiv").eq(1).css("display")).toBe("none");
    });
    it('shows cards matching a data attribute', function () {
      $("#id_filter").val("addr2");
      home.changeFiltering(null);
      expect($(".cardiv").eq(1).css("display")).not.toBe("none");
    });
  });
});
