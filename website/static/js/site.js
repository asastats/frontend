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
  // initializeCookieConsent();
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
/**
 * Initialize cookie consent widget
 * @function initializeCookieConsent
 *
 */
/* istanbul ignore next */
function initializeCookieConsent() {
  silktideCookieBannerManager.updateCookieBannerConfig({
    background: {
      showBackground: true
    },
    cookieIcon: {
      position: "bottomLeft"
    },
    cookieTypes: [
      {
        id: "necessary",
        name: "Necessary",
        description: "<p>These cookies are necessary for the website to function properly and cannot be switched off. They help with things like logging in and setting your privacy preferences.</p>",
        required: true,
        onAccept: function() {
          console.log('Add logic for the required Necessary here');
        }
      },
      {
        id: "analytics",
        name: "Analytics",
        description: "<p>These cookies help us improve the site by tracking which pages are most popular and how visitors move around the site.</p>",
        defaultValue: true,
        onAccept: function() {
          gtag('consent', 'update', {
            analytics_storage: 'granted',
          });
          dataLayer.push({
            'event': 'consent_accepted_analytics',
          });
        },
        onReject: function() {
          gtag('consent', 'update', {
            analytics_storage: 'denied',
          });
        }
      },
      {
        id: "advertising",
        name: "Advertising",
        description: "<p>These cookies provide extra features and personalization to improve your experience. They may be set by us or by partners whose services we use.</p>",
        onAccept: function() {
          gtag('consent', 'update', {
            ad_storage: 'granted',
            ad_user_data: 'granted',
            ad_personalization: 'granted',
          });
          dataLayer.push({
            'event': 'consent_accepted_advertising',
          });
        },
        onReject: function() {
          gtag('consent', 'update', {
            ad_storage: 'denied',
            ad_user_data: 'denied',
            ad_personalization: 'denied',
          });
        }
      }
    ],
    text: {
      banner: {
        description: "<p>We use cookies on our site to enhance your user experience, provide personalized content, and analyze our traffic. <a href=\"https://your-website.com/cookie-policy\" target=\"_blank\">Cookie Policy.</a></p>",
        acceptAllButtonText: "Accept all",
        acceptAllButtonAccessibleLabel: "Accept all cookies",
        rejectNonEssentialButtonText: "Reject non-essential",
        rejectNonEssentialButtonAccessibleLabel: "Reject non-essential",
        preferencesButtonText: "Preferences",
        preferencesButtonAccessibleLabel: "Toggle preferences"
      },
      preferences: {
        title: "Customize your cookie preferences",
        description: "<p>We respect your right to privacy. You can choose not to allow some types of cookies. Your cookie preferences will apply across our website.</p>",
        creditLinkText: "Get this banner for free",
        creditLinkAccessibleLabel: "Get this banner for free"
      }
    }
  });
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
