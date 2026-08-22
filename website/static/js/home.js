/**
 * @file Sorting and filtering bundle names on home page browser side
 * @author Ivica Paleka
 */

/**
 * Call main function upon finished document loading
 *
 */
$(mainHome);


/**
 * Main function
 * @function mainHome
 *
 */
function mainHome() {
  $("input[type=radio][name=sort]").on("change", changeSorting);
  $("#id_desc").on("change", changeDescending);
  $("#id_filter").on("change paste keyup", changeFiltering);
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Panel input events
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Change order of bundlename cards when descending checked value changes.
 * @function changeDescending
 *
 * @param {jQuery} event Triggered change event object
 *
 */
function changeDescending(event) {
  $(".bundlenames > div").each(function () {
    $(this).prependTo(this.parentNode);
  });
}


/**
 * Change order of bundlename cards when sorting radio option changes.
 * @function changeSorting
 *
 * @param {jQuery} event Triggered change event object
 *
 */
function changeSorting(event) {
  /**
   * Should ordering be descending or not (-1 or 1)
   * @type {Number}
   */
  var desc = $('#id_desc').is(":checked") ? -1 : 1;
  /**
   * Field to sort divs by
   * @type {String}
   */
  var field = this.id.slice(3, this.id.length);
  $(".bundlenames").each(function () {
    $(this).html($(this).children("div").sort(function (a, b) {
      return ($(b).data(field)) < ($(a).data(field)) ? desc : -1 * desc;
    }));
  });
}


/**
 * Show only cards having entered text in any of their data attributes.
 * @function changeFiltering
 *
 * @param {jQuery} event Triggered change event object
 *
 */
function changeFiltering(event) {
  /**
   * Array of bundlename cards
   * @type {Array.<Object>}
   */
  var cards;
  /**
   * Entered text to filter by
   * @type {String}
   */
  var value = $("#id_filter").val().toLowerCase();

  if (value == "") {
    $(".cardiv").show();
  } else {
    $(".cardiv").hide();
    // The data attributes only. There used to be a fifth pass reading
    // `$(this).children().children().attr('title')`, which on every row was the
    // literal string "Evaluate bundle" -- so typing "eval" revealed the whole
    // list and the title matched nothing anybody would search for. It also tied
    // the filter to how deeply the row happened to be nested.
    ["name", "addresses", "created", "modified"].forEach(function (attr) {
      cards = $('.cardiv').filter(function () {
        return ($(this).attr('data-' + attr) || "").toLowerCase().indexOf(value) > -1;
      });
      cards.show();
    });
  }
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: exports needed by jest testing framework
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/* istanbul ignore next */
if (typeof exports !== 'undefined') {
  module.exports = {
    mainHome,
    changeDescending,
    changeSorting,
    changeFiltering,
  };
}
