/**
 * @jest-environment jsdom
 */

"use strict";

function run() {
  jest.resetModules();
  require("../static/js/api-back.js");
}

function clickWithHistory(length) {
  Object.defineProperty(window.history, "length", { configurable: true, value: length });
  window.history.back = jest.fn();
  document.body.innerHTML = '<a id="api-back" href="/">Back</a>';
  run();
  const event = new MouseEvent("click", { bubbles: true, cancelable: true });
  document.getElementById("api-back").dispatchEvent(event);
  return event;
}

describe("api-back.js", () => {
  test("goes back in history when there is one", () => {
    const event = clickWithHistory(2);
    expect(window.history.back).toHaveBeenCalledTimes(1);
    expect(event.defaultPrevented).toBe(true);
  });

  test("follows the link when there is none", () => {
    const event = clickWithHistory(1);
    expect(window.history.back).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);
  });

  test("does nothing on a page without it", () => {
    document.body.innerHTML = "";
    expect(run).not.toThrow();
  });
});
