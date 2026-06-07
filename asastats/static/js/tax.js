/**
 * @file www.asastats.com browser side logic tax page functions
 * @author Ivica Paleka
 */

/*
* * * * * * * * * * * * * * * * * * * * * * * * * * *
* SECTION: Initialization
* * * * * * * * * * * * * * * * * * * * * * * * * * *
*/

/**
 * Call main function upon finished document loading
 *
 */
$(mainTax);


/**
 * Main function
 * @function mainTax
 *
 */
function mainTax() {
  $(window).on('pageshow', setDefault);
  $('.providertip').tooltip();
  $("#download").on('click', removeError);
  $("#back").on('click', setProgress);
  $("#process_form").on('submit', disableProcessSubmit);
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Disable submit button in the process form
 * @function disableProcessSubmit
 *
 * @param {jQuery} event Triggered event object
 *
 */
function disableProcessSubmit(event) {
  setTimeout(function () { $('#process').attr('disabled', 'disabled'); }, 1);
}


/**
 * Reset appearance to default - remove progress
 * @function setDefault
 *
 * @param {jQuery} event Triggered pageshow event object
 *
 */
function setDefault(event) {
  $("body").css("cursor", "default");
  $('.indeterminate').parent().removeClass('progress');
  $('#process').prop("disabled", false);
  $('#download').prop("disabled", false);
  $('#refresh').prop("disabled", false);
  $('#back').removeClass("disabled");
}


/**
 * Set appearance to progress
 * @function setProgress
 *
 * @param {jQuery} event Triggered click event object
 *
 */
function setProgress(event) {
  $('.indeterminate').parent().addClass('progress');
  $("body").css("cursor", "progress");
  removeError(null);
  setTimeout(function () { $('#back').addClass('disabled'); }, 1);
  setTimeout(function () { $('#download').attr('disabled', 'disabled'); }, 1);
  setTimeout(function () { $('#refresh').attr('disabled', 'disabled'); }, 1);
}


/**
 * Remove error from the page
 * @function removeError
 *
 * @param {jQuery} event Triggered change event object
 *
 */
function removeError(event) {
  $('.errorlist').remove();
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: exports needed by jest testing framework
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/* istanbul ignore next */
if (typeof exports !== 'undefined') {
  module.exports = {
    mainTax
  };
}
