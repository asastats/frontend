/**
 * @file Manipulating emails browser side logic
 * @author Ivica Paleka
 */

 /*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Global variables declaration
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Constant holding globally required constant values.
 * @constant {Object}
 *
 */
var CONSTANTS;


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Setup
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Call main function upon finished document loading
 *
 */
$(mainEmails);


/**
 * Main function
 * @function mainEmails
 *
 */
function mainEmails() {
  CONSTANTS = {
    "m": {
      "rme": "Are you sure you want to remove the selected email address?",
      "rve": "Are you sure you want to re-send a verification email?"
    }
  };
  $("button[name='action_remove']").on("click", openModalConfirmRemoveEmail);
  $("button[name='action_send']").on("click", openModalConfirmResendVerification);
  $("#id_confirm").on("click", submitEmailAction);
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Instantiate and open modal window.
 * @function openModalConfirm
 *
 * @param {String} typ Identifier of confirmation type
 *
 */
function openModalConfirm(typ) {
  $("#id_pconfirm").text(CONSTANTS.m[typ]);
  $("#id_confirm")[0].dataset.target = typ;
  /**
   * Modal div element
   * @type {Object}
   */
  var modal = document.querySelector("#id_modalconfirm");
  /**
   * Instantiated bottom sheet modal object
   * @type {Object}
   */
  var instance = M.Modal.getInstance(modal);
  instance.open();
}


/**
 * Open modal for user to confirm email removing.
 * @function openModalConfirmRemoveEmail
 *
 * @param {Object} event Triggered event
 *
 */
function openModalConfirmRemoveEmail(event) {
  event.preventDefault();
  openModalConfirm("rme");
}


/**
 * Open modal for user to confirm re-sending email verification.
 * @function openModalConfirmResendVerification
 *
 * @param {Object} event Triggered event
 *
 */
function openModalConfirmResendVerification(event) {
  event.preventDefault();
  openModalConfirm("rve");
}


/**
 * User has confirmed action through the confirmation dialog.
 * @function submitEmailAction
 *
 * @param {jQuery} event Triggered event object
 *
 */
function submitEmailAction(event) {
  /**
   * Name of submit action to take
   * @type {String}
   */
  var action;
  /**
   * Confirmation dialog type indicator
   * @type {String}
   */
  var target = $("#id_confirm")[0].dataset.target;
  if (target == "rme")
    action = "action_remove"
  else
    action = "action_send"
  $("button[name='" + action + "']").off("click");
  $("button[name='" + action + "']").trigger("click");
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: exports needed by jest testing framework
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/* istanbul ignore next */
if (typeof exports !== 'undefined') {
  module.exports = {
    mainEmails,
    openModalConfirm,
    openModalConfirmRemoveEmail,
    openModalConfirmResendVerification,
    submitEmailAction,
  };
}
