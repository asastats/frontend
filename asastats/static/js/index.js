/**
 * @file www.asastats.com browser side logic index page
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
$(mainIndex);

/**
 * Main function
 * @function mainIndex
 *
 */
function mainIndex() {
  $(window).on('pageshow', setDefault);
  $("#id_address").on('change paste keyup click', removeError);
  $("#id_address").on('keydown', setTextarea);
  $('.prefix').on('click', replaceTextarea);
  $("#whenmoon").on('click', setProgress);
  $(".ns").on('click', addNS);
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Add name service suffix to name
 * @function addNS
 *
 */
function addNS() {
  var value = $('#id_address').val();
  var index = value.toLowerCase().indexOf("/ans");
  if (index > -1)
    value = value.slice(0, value.length - 4);
  else if (value.toLowerCase().indexOf("/nfd") > -1)
    value = value.slice(0, value.length - 4);
  $('#id_address').val(value + "/" + $(this).attr('id'));
  $('#id_address').focus();
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
  $('#whenmoon').prop("disabled", false); 
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
  setTimeout(function () { $('#whenmoon').attr('disabled', 'disabled'); }, 1);
}


/**
 * Return html textarea element
 * @function createTextarea
 *
 * @param {String} value value entered in address input box
 *
 */
function createTextarea(value) {
  return '<textarea id="id_addresses" name="addresses" class="materialize-textarea" autofocus="autofocus" placeholder="Enter up to five Algorand addresses" >' + value + '</textarea>';
}

/**
 * Replace input element with textarea
 * @function replaceTextarea
 *
 */
function replaceTextarea() {
  var value = $('#id_address').val();
  $('.prefix').hide();
  $('#id_address').replaceWith(createTextarea(value));
  M.textareaAutoResize($('#id_addresses'));
  updateBundle();
  $("#id_addresses").on('change', updateBundle);
  $('#id_addresses').focus();
}


/**
 * Change input from text to textarea
 * @function setTextarea
 *
 * @param {jQuery} event Triggered keydown event object
 *
 */
function setTextarea(event) {
  if (event.keyCode == 32 && $(this).val().length >= 58)
    replaceTextarea()
}


/**
 * Update hidden bundle field with textarea value
 * @function updateBundle
 *
 */
function updateBundle() {
  $('#id_bundle').val($('#id_addresses').val());
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: exports needed by jest testing framework
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/* istanbul ignore next */
if (typeof exports !== 'undefined') {
  module.exports = {
    mainIndex,
    removeError,
    setDefault,
    setProgress,
    setTextarea,
    updateBundle
  };
}
