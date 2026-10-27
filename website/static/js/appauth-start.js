/**
 * @file Sends the app's sign-in on to the provider at once (appauth/start.html).
 * @description A file rather than an inline script, for the CSP.
 */

(function () {
  "use strict";
  var form = document.getElementById("id_app_auth_start");
  if (form) form.submit();
})();
