/**
 * @file website's browser side logic index page
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


// localStorage key and cap for the app's checked addresses; see docs/logbook.md.
var RECENT_KEY = 'asastats.recentAddresses';
var RECENT_LIMIT = 20;
var ADDRESS_PATTERN = /^[A-Z2-7]{58}$/;
var NAME_PATTERN = /^[a-z0-9-]+(?:\.[a-z0-9-]+)*\.algo(?:\/(?:ans|nfd))?$/i;

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
  $("#track").on('click', setProgress);
  $(".ns").on('click', addNS);
  if ($('html').hasClass('in-app')) {
    $("#id_form").on('submit', rememberEntries);
    showRecentEntries();
  }
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
  $('#track').prop("disabled", false); 
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
  setTimeout(function () { $('#track').attr('disabled', 'disabled'); }, 1);
}


/**
 * Return html textarea element
 * @function createTextarea
 *
 * @param {String} value value entered in address input box
 *
 */
function createTextarea(value) {
  return '<textarea id="id_addresses" name="addresses" class="textarea w-full [field-sizing:content]" rows="3" autofocus="autofocus" placeholder="Enter up to five Algorand addresses" >' + value + '</textarea>';
}

/**
 * Replace input element with textarea
 * @function replaceTextarea
 *
 */
function replaceTextarea() {
  var value = $('#id_address').val();
  $('.prefix').hide();
  hideRecentEntries();
  $('#id_address').replaceWith(createTextarea(value));
  // `M.textareaAutoResize` grew the box as addresses were pasted in. CSS
  // `field-sizing: content` does the same thing without a framework, and the
  // textarea's `rows` is a usable floor where it is unsupported.

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
 * Return true for an Algorand address or a .algo name
 * @function isRememberable
 *
 * @param {*} entry value to check
 * @return {Boolean}
 */
function isRememberable(entry) {
  return typeof entry === 'string' &&
    (ADDRESS_PATTERN.test(entry) || NAME_PATTERN.test(entry));
}


/**
 * Return the app's previously checked entries, newest first
 * @function recentEntries
 *
 * @return {Array} stored entries, or an empty array
 */
function recentEntries() {
  try {
    var stored = JSON.parse(localStorage.getItem(RECENT_KEY));
    return Array.isArray(stored) ? stored.filter(isRememberable) : [];
  } catch (error) {
    return [];
  }
}


/**
 * Store the addresses and names being submitted, newest first
 * @function rememberEntries
 *
 */
function rememberEntries() {
  var source = $('#id_addresses').length ? $('#id_addresses') : $('#id_address');
  var entered = String(source.val() || '').split(/[\s,]+/).filter(isRememberable);
  if (!entered.length)
    return;
  var entries = entered.concat(recentEntries()).filter(function (entry, position, all) {
    return all.indexOf(entry) === position;
  }).slice(0, RECENT_LIMIT);
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(entries));
  } catch (error) {
    // Storage unavailable: the entry is simply not remembered.
  }
}


/**
 * Remove one entry from the stored ones
 * @function forgetEntry
 *
 * @param {String} entry the entry to remove
 */
function forgetEntry(entry) {
  var entries = recentEntries().filter(function (stored) {
    return stored !== entry;
  });
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(entries));
  } catch (error) {
    // Storage unavailable: nothing to forget.
  }
}


/**
 * Hide the suggestion list
 * @function hideRecentEntries
 *
 */
function hideRecentEntries() {
  $('#id_address_history').addClass('hidden');
}


/**
 * Fill the suggestion list with stored entries matching the address input
 * @function renderRecentEntries
 *
 */
function renderRecentEntries() {
  var list = $('#id_address_history');
  var typed = String($('#id_address').val() || '').toLowerCase();
  var matches = recentEntries().filter(function (entry) {
    return entry.toLowerCase().indexOf(typed) > -1;
  });
  list.empty();
  if (!$('#id_address').length || !matches.length) {
    hideRecentEntries();
    return;
  }
  matches.forEach(function (entry) {
    var row = $('<li class="flex min-w-0 items-center gap-1 rounded-field hover:bg-base-200"></li>');
    row.append($('<button type="button" class="recent-entry min-w-0 flex-1 truncate px-3 py-2 text-left text-sm"></button>')
      .attr('data-entry', entry).text(entry));
    row.append($('<button type="button" class="recent-forget btn btn-ghost btn-xs btn-circle">&#x2715;</button>')
      .attr({'data-entry': entry, 'aria-label': 'Forget ' + entry}));
    list.append(row);
  });
  list.removeClass('hidden');
}


/**
 * Handle a tap on the suggestion list: pick or forget an entry
 * @function chooseRecentEntry
 *
 * @param {jQuery} event Triggered click event object
 */
function chooseRecentEntry(event) {
  var target = $(event.target).closest('[data-entry]');
  if (!target.length)
    return;
  if (target.hasClass('recent-forget')) {
    forgetEntry(target.attr('data-entry'));
    renderRecentEntries();
    return;
  }
  $('#id_address').val(target.attr('data-entry')).focus();
  removeError(null);
  hideRecentEntries();
}


/**
 * Hide the suggestion list on Escape
 * @function closeRecentOnEscape
 *
 * @param {jQuery} event Triggered keydown event object
 */
function closeRecentOnEscape(event) {
  if (event.key === 'Escape')
    hideRecentEntries();
}


/**
 * Offer previously checked entries below the address input
 * @function showRecentEntries
 *
 */
function showRecentEntries() {
  var input = $('#id_address');
  $('#id_address_history').remove();
  // `#id_address_history` and its classes are asserted by tests and functional tests.
  var list = $('<ul id="id_address_history" class="absolute z-10 mt-1 w-full list-none overflow-y-auto rounded-box border border-base-300 bg-base-100 p-1 shadow-lg hidden"></ul>')
    .css({left: 0, top: '100%', maxHeight: '15rem', overflowX: 'hidden'});
  // Keep the input focused while a row is tapped, so blur does not hide the list first.
  list.on('mousedown', function (event) { event.preventDefault(); });
  list.on('click', chooseRecentEntry);
  input.parent().addClass('relative').append(list);
  input.on('focus click input', renderRecentEntries);
  input.on('blur', hideRecentEntries);
  input.on('keydown', closeRecentOnEscape);
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
    chooseRecentEntry,
    closeRecentOnEscape,
    forgetEntry,
    hideRecentEntries,
    isRememberable,
    mainIndex,
    recentEntries,
    rememberEntries,
    removeError,
    renderRecentEntries,
    setDefault,
    setProgress,
    setTextarea,
    showRecentEntries,
    updateBundle
  };
}
