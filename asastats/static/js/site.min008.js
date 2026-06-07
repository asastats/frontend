/**
 * @file www.asastats.com browser side logic initialization and setup functions
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
$(mainSite);

/**
 * Main function
 * @function mainSite
 *
 */
function mainSite() {
  $('.sidenav').sidenav();
  $('.modal').modal();
  $('.publictip').tooltip();
  checkMode();
  if (isDark())
    toggleText();
  $('.dark-toggle').on('click', toggleMode);
  $(".copy").on("click", copyToClipboard);
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Check if user has saved Dark mode in local storage
 * @function checkMode
 *
 */
function checkMode() {
  if (isDark()) {
    document.querySelector('body').classList.add('dark');
    $("#logo").attr("src", "/static/logo-dark.png");
    $("#brand").attr("src", "/static/asastats-dark.png");
    $("#cpr").addClass("mydark-text");
  } else {
    document.querySelector('body').classList.remove('dark');
    $("#logo").attr("src", "/static/logo.png");
    $("#brand").attr("src", "/static/asastats.png");
  }
}


/**
 * Copy previous element's text to clipboard
 * @function copyToClipboard
 *
 * @param {jQuery} event Triggered click event object
 *
 */
function copyToClipboard(event) {
  var link = $(this).prev();
  if (navigator.clipboard) {
    var color = link.css("color");
    navigator.clipboard.writeText(link.text());
    link.css("color", "#ababab");
    setTimeout(function () { link.css("color", color); }, 500);
  }
}


/**
 * Return true if current mode from data variable or localStorage is true
 * @function isDark
 *
 */
 function isDark() {
   return (document.getElementById("footer").dataset.mode === "dark" || localStorage.getItem("mode") === "dark");
}



/**
 * Toggle bright/dark mode
 * @function toggleMode
 *
 * @param {jQuery} event Triggered click event object
 *
 */
function toggleMode(event) {
  localStorage.setItem('mode',
    (localStorage.getItem('mode') || 'light') === 'light' ? 'dark' : 'light'
  );
  checkMode();
  toggleText();
}


/**
 * Toggle text properties for mode
 * @function toggleText
 *
 */
function toggleText() {
  $(".dark-toggle").toggleClass("brightbtn darkbtn");
  $(".txt").toggleClass("mydark-text myredlight-text");
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: exports needed by jest testing framework
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/* istanbul ignore next */
if (typeof exports !== 'undefined') {
  module.exports = {
    mainSite,
    checkMode,
    toggleMode,
    toggleText
  };
}
