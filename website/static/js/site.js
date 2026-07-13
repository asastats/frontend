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
  $('.sidenav').sidenav();
  $('.modal').modal();
  initLoginModalTabs();
  checkMode();
  if (isDark())
    toggleText();
  $('.dark-toggle').on('click', toggleMode);
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
 * Check if user has saved Dark mode in local storage
 * @function checkMode
 *
 */
function checkMode() {
  if (isDark()) {
    document.documentElement.classList.add('dark');
    $("#logo").attr("src", "/static/logo-dark.png");
    $("#brand").attr("src", "/static/asastats-dark.png");
    $("#cpr").addClass("mydark-text");
  } else {
    document.documentElement.classList.remove('dark');
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
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Proprietary widgets and objects initialization functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Initialize the login modal's content tabs and keep the active indicator
 * correct. Materialize tabs initialized inside a hidden modal cannot measure
 * their width, so the default ("Log in") underline is missing until the user
 * interacts; refreshing it on modal open fixes that. Safely does nothing on
 * pages where the modal is not rendered (e.g. for authenticated users).
 * @function initLoginModalTabs
 *
 */
function initLoginModalTabs() {
  var modalEl = document.getElementById('modalLogin');
  if (!modalEl) {
    return;
  }
  var tabsEl = modalEl.querySelector('.tabs');
  if (!tabsEl || typeof M === 'undefined' || !M.Tabs) {
    return;
  }
  var tabs = M.Tabs.getInstance(tabsEl) || M.Tabs.init(tabsEl);
  var modal = M.Modal && M.Modal.getInstance(modalEl);
  if (modal) {
    modal.options.onOpenEnd = function () {
      tabs.updateTabIndicator();
    };
  }
}

/**
 * Open the login modal when an anonymous visitor clicks a Swap button.
 *
 * The address accordion is cached across users, so its per-asset Swap links are
 * shown to everyone and point at the "swap_source" URL (which redirects
 * anonymous users to the login page). The login modal is rendered only for
 * anonymous visitors, so its presence is the per-user signal: when it exists,
 * intercept the click and open the modal; otherwise (authenticated) let the swap
 * controller load its inline panel. If Materialize is unavailable, the click is
 * left to navigate to "swap_source", which redirects to the login page.
 * @function swapLoginGate
 *
 * @param {jQuery} event Triggered click event object
 *
 */
function swapLoginGate(event) {
  var modalEl = document.getElementById('modalLogin');
  var modal = modalEl && typeof M !== 'undefined' && M.Modal
    ? M.Modal.getInstance(modalEl)
    : null;
  if (!modal) {
    // No initialized login modal on this page (authenticated user, or the modal
    // was cached out): let the click navigate to swap_source, which redirects to
    // the login page.
    return;
  }
  event.preventDefault();
  // Record the intended swap URL on the modal's hidden login field. Both login
  // paths read it from there: the email/password form submits it, and the wallet
  // flow reads its value at verify time. This field is static markup in
  // modal_login.html (always present, never re-rendered by the wallet bundle),
  // so it avoids the race of stamping the wallet tab's own markup at click time.
  var nextInput = document.getElementById('id_modal_login_next');
  if (nextInput) {
    nextInput.value = event.currentTarget.getAttribute('href') || '';
  }
  modal.open();
}

/**
 * Turn a ``?swap_error=<code>`` query param (set by a server-side swap redirect)
 * into a Materialize toast, then strip the param so a refresh doesn't repeat it.
 * @function showSwapErrorToast
 *
 */
function showSwapErrorToast() {
  var params = new URLSearchParams(window.location.search);
  var code = params.get('swap_error');
  if (!code) {
    return;
  }
  var messages = {
    unlinked: 'You can only swap from an address linked to your account.'
  };
  if (typeof M !== 'undefined' && M.toast) {
    M.toast({ html: messages[code] || 'Swap is not available.' });
  }
  params.delete('swap_error');
  var query = params.toString();
  window.history.replaceState(
    {},
    document.title,
    window.location.pathname + (query ? '?' + query : '') + window.location.hash
  );
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
    checkMode,
    toggleMode,
    toggleText,
    initLoginModalTabs,
    swapLoginGate,
    showSwapErrorToast
  };
}
