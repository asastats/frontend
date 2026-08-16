/**
 * @file website's browser side logic initialization and setup functions
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
  // Materialize is gone from the project, so `.sidenav()` and `.modal()` --
  // its jQuery plugins -- have nothing to initialise and no markup to find.
  // The appearance controls went with it: `checkMode`/`toggleMode` swapped
  // logo images and text classes that only the old base rendered. theme.js
  // owns appearance now, through `<html data-theme>`.
  $(".copy").on("click", copyToClipboard);
  $(document)
    .off("click.swapgate")
    .on("click.swapgate", ".id-swap-swap-toggle", swapLoginGate);
  showSwapErrorToast();
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */


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


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Proprietary widgets and objects initialization functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */


/**
 * Open the login dialog when an anonymous visitor clicks a Swap button.
 *
 * The address accordion is cached across users, so its per-asset Swap links are
 * shown to everyone and point at the "swap_source" URL (which redirects
 * anonymous users to the login page). The dialog is rendered only for anonymous
 * visitors, so its presence is the per-user signal: when it exists, intercept
 * the click and open it; otherwise (authenticated) let the swap controller load
 * its inline panel.
 *
 * The dialog is a native <dialog> driven by authmodal.js. This used to go
 * through `M.Modal.getInstance`, which returns null now that Materialize is
 * gone -- so every anonymous Swap click fell through to a full-page redirect
 * instead of opening the dialog in place.
 * @function swapLoginGate
 *
 * @param {jQuery} event Triggered click event object
 *
 */
function swapLoginGate(event) {
  var dialog = document.getElementById('modalLogin');
  if (!dialog || !dialog.showModal) {
    // No dialog on this page (authenticated user, or the markup was cached
    // out): let the click navigate to swap_source, which redirects to login.
    return;
  }
  event.preventDefault();
  // Record the intended swap URL on the dialog's hidden login field. Both login
  // paths read it from there: the email/password form submits it, and the wallet
  // flow reads its value at verify time. This field is static markup in
  // modal_login.html (always present, never re-rendered by the wallet bundle),
  // so it avoids the race of stamping the wallet tab's own markup at click time.
  var nextInput = document.getElementById('id_modal_login_next');
  if (nextInput) {
    nextInput.value = event.currentTarget.getAttribute('href') || '';
  }
  if (!dialog.open) dialog.showModal();
}

/**
 * Turn a ``?swap_error=<code>`` query param (set by a server-side swap redirect)
 * into an on-page notice, then strip the param so a refresh doesn't repeat it.
 *
 * This was `M.toast`, which silently did nothing once Materialize was removed
 * -- the redirect happened and the reason for it was never shown.
 * @function showSwapErrorToast
 *
 */
function showSwapErrorToast() {
  var params = new URLSearchParams(window.location.search);
  var code = params.get('swap_error');
  if (code) {
    var messages = {
      unlinked: 'You can only swap from an address linked to your account.'
    };
    var notice = document.createElement('div');
    notice.className = 'alert alert-error fixed bottom-4 left-1/2 z-50 w-max max-w-[90vw] -translate-x-1/2';
    notice.setAttribute('role', 'alert');
    notice.textContent = messages[code] || 'Swap is not available.';
    document.body.appendChild(notice);
    setTimeout(function () { notice.remove(); }, 6000);

    params.delete('swap_error');
    var query = params.toString();
    window.history.replaceState(
      {},
      document.title,
      window.location.pathname + (query ? '?' + query : '') + window.location.hash
    );
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
    mainSite,
    swapLoginGate,
    showSwapErrorToast
  };
}
