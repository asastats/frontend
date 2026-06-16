const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

global.M = { Modal: { getInstance: jest.fn() } };

const emails = require('../static/js/emails.js');

const fixture =
  '<button name="action_remove"></button>' +
  '<button name="action_send"></button>' +
  '<p id="id_pconfirm"></p>' +
  '<a id="id_confirm"></a>' +
  '<div id="id_modalconfirm"></div>';

let modalInstance;

beforeEach(() => {
  document.body.innerHTML = fixture;
  modalInstance = { open: jest.fn() };
  M.Modal.getInstance.mockReturnValue(modalInstance);
  emails.mainEmails();
});

afterEach(() => {
  jest.resetModules();
});


describe("in SECTION: Setup", function () {

  describe("mainEmails function", function () {
    it('binds click handlers for the email action buttons', function () {
      $("button[name='action_remove']").off("click");
      $("button[name='action_send']").off("click");
      $("#id_confirm").off("click");
      emails.mainEmails();
      expect(getEvents($("button[name='action_remove']")[0]).click[0]
        .handler.name).toBe("openModalConfirmRemoveEmail");
      expect(getEvents($("button[name='action_send']")[0]).click[0]
        .handler.name).toBe("openModalConfirmResendVerification");
      expect(getEvents($("#id_confirm")[0]).click[0].handler.name)
        .toBe("submitEmailAction");
    });
  });
});


describe("in SECTION: Helper functions", function () {

  describe("openModalConfirm function", function () {
    it('sets the message and opens the modal', function () {
      emails.openModalConfirm("rme");
      expect($("#id_pconfirm").text()).toContain("remove the selected email");
      expect($("#id_confirm")[0].dataset.target).toBe("rme");
      expect(modalInstance.open).toHaveBeenCalledWith();
    });
  });

  describe("openModalConfirmRemoveEmail function", function () {
    it('prevents default and opens the remove confirmation', function () {
      var event = { preventDefault: jest.fn() };
      emails.openModalConfirmRemoveEmail(event);
      expect(event.preventDefault).toHaveBeenCalledWith();
      expect($("#id_confirm")[0].dataset.target).toBe("rme");
    });
  });

  describe("openModalConfirmResendVerification function", function () {
    it('prevents default and opens the resend confirmation', function () {
      var event = { preventDefault: jest.fn() };
      emails.openModalConfirmResendVerification(event);
      expect(event.preventDefault).toHaveBeenCalledWith();
      expect($("#id_confirm")[0].dataset.target).toBe("rve");
    });
  });

  describe("submitEmailAction function", function () {
    it('triggers the remove action when target is rme', function () {
      var handler = jest.fn();
      document.querySelector("button[name='action_remove']")
        .addEventListener("click", handler);
      $("#id_confirm")[0].dataset.target = "rme";
      emails.submitEmailAction(null);
      expect(handler).toHaveBeenCalled();
    });
    it('triggers the send action otherwise', function () {
      var handler = jest.fn();
      document.querySelector("button[name='action_send']")
        .addEventListener("click", handler);
      $("#id_confirm")[0].dataset.target = "rve";
      emails.submitEmailAction(null);
      expect(handler).toHaveBeenCalled();
    });
  });
});
