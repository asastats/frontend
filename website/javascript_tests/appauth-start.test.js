/**
 * @jest-environment jsdom
 */

"use strict";

function run() {
  jest.resetModules();
  require("../static/js/appauth-start.js");
}

describe("appauth-start.js", () => {
  test("submits the start form", () => {
    document.body.innerHTML = '<form id="id_app_auth_start"></form>';
    const form = document.getElementById("id_app_auth_start");
    form.submit = jest.fn();
    run();
    expect(form.submit).toHaveBeenCalledTimes(1);
  });

  test("does nothing on a page without it", () => {
    document.body.innerHTML = "";
    expect(run).not.toThrow();
  });
});
