/**
 * @jest-environment jsdom
 */

"use strict";

let added = [];

/** Load the script afresh, recording its listeners so afterEach can drop them. */
function run({ inApp = true } = {}) {
  document.documentElement.classList.toggle("in-app", inApp);
  jest.resetModules();
  const docAdd = jest.spyOn(document, "addEventListener");
  const winAdd = jest.spyOn(window, "addEventListener");
  require("../static/js/pullrefresh.js");
  docAdd.mock.calls.forEach(([type, fn]) => added.push([document, type, fn]));
  winAdd.mock.calls.forEach(([type, fn]) => added.push([window, type, fn]));
  docAdd.mockRestore();
  winAdd.mockRestore();
}

function touch(type, points, target = document.body) {
  const event = new Event(type, { bubbles: true });
  Object.defineProperty(event, "touches", {
    value: points.map(([clientX, clientY]) => ({ clientX, clientY })),
  });
  target.dispatchEvent(event);
}

/** Start at (100, 100) and move the finger down by each of `dys`. */
function pull(dys, target) {
  touch("touchstart", [[100, 100]], target);
  dys.forEach((dy) => touch("touchmove", [[100, 100 + dy]], target));
}

const indicator = () => document.getElementById("pull-refresh");

beforeEach(() => {
  document.body.innerHTML = "<main><p id='text'>Holdings</p></main>";
  window.scrollY = 0;
  window.reloadPage = jest.fn();
});

afterEach(() => {
  added.forEach(([target, type, fn]) => target.removeEventListener(type, fn));
  added = [];
  delete window.reloadPage;
  document.documentElement.classList.remove("in-app");
});

describe("pullrefresh.js", () => {
  test("does nothing in a browser", () => {
    run({ inApp: false });
    pull([200]);
    touch("touchend", []);
    expect(indicator()).toBeNull();
    expect(window.reloadPage).not.toHaveBeenCalled();
  });

  test("a long pull from the top shows the ready indicator and reloads on release", () => {
    run();
    pull([60, 200]);
    const el = indicator();
    expect(el.getAttribute("aria-hidden")).toBe("true");
    expect(el.classList.contains("ready")).toBe(true);
    expect(el.classList.contains("dragging")).toBe(true);
    expect(el.style.opacity).toBe("1");
    touch("touchend", []);
    expect(window.reloadPage).toHaveBeenCalledTimes(1);
    expect(el.classList.contains("spinning")).toBe(true);
    expect(el.classList.contains("dragging")).toBe(false);
  });

  test("the indicator stops at its limit however far the finger goes", () => {
    run();
    pull([1000]);
    expect(indicator().style.transform).toBe("translate(-50%, 96px) rotate(384deg)");
  });

  test("a short pull shows the indicator, then hides it without reloading", () => {
    run();
    pull([60]);
    const el = indicator();
    expect(el.classList.contains("ready")).toBe(false);
    expect(el.style.opacity).toBe(String(30 / 64));
    touch("touchend", []);
    expect(window.reloadPage).not.toHaveBeenCalled();
    expect(el.style.opacity).toBe("0");
    expect(el.style.transform).toBe("");
  });

  test("pulling back up before letting go cancels the refresh", () => {
    run();
    pull([200, -50]);
    expect(indicator().classList.contains("ready")).toBe(false);
    touch("touchend", []);
    expect(window.reloadPage).not.toHaveBeenCalled();
  });

  test("the indicator is created once and reused", () => {
    run();
    pull([60]);
    touch("touchend", []);
    pull([60]);
    expect(document.querySelectorAll("#pull-refresh")).toHaveLength(1);
  });

  test("falls back to a plain reload without address.js", () => {
    delete window.reloadPage;
    const error = jest.spyOn(console, "error").mockImplementation(() => {});
    run();
    pull([200]);
    touch("touchend", []);
    // jsdom cannot navigate and says so: that is the reload being asked for.
    expect(error.mock.calls.flat().join(" ")).toMatch(/navigation/);
    error.mockRestore();
  });

  test.each([
    ["the page is scrolled", () => { window.scrollY = 10; }],
    ["two fingers touch", null],
    ["a dialog is open", () => { document.body.insertAdjacentHTML("beforeend", "<dialog open></dialog>"); }],
  ])("no pull starts when %s", (_, arrange) => {
    run();
    if (arrange) {
      arrange();
      pull([200]);
    } else {
      touch("touchstart", [[100, 100], [150, 100]]);
      touch("touchmove", [[100, 300], [150, 300]]);
    }
    touch("touchend", []);
    expect(indicator()).toBeNull();
    expect(window.reloadPage).not.toHaveBeenCalled();
  });

  test.each(["input", "textarea", "select"])("no pull starts in a %s", (tag) => {
    run();
    const field = document.createElement(tag);
    document.body.appendChild(field);
    pull([200], field);
    touch("touchend", [], field);
    expect(window.reloadPage).not.toHaveBeenCalled();
  });

  test("no pull starts inside a box that is itself scrolled", () => {
    run();
    const box = document.createElement("div");
    box.innerHTML = "<span>row</span>";
    document.body.appendChild(box);
    Object.defineProperty(box, "scrollTop", { value: 40 });
    pull([200], box.firstChild);
    touch("touchend", [], box.firstChild);
    expect(window.reloadPage).not.toHaveBeenCalled();
  });

  test("a touch reported on the document itself still pulls", () => {
    run();
    pull([200], document);
    touch("touchend", [], document);
    expect(window.reloadPage).toHaveBeenCalledTimes(1);
  });

  test.each([
    ["upward", [100, 60]],
    ["sideways", [180, 120]],
  ])("an %s first move is a scroll, not a pull", (_, [x, y]) => {
    run();
    touch("touchstart", [[100, 100]]);
    touch("touchmove", [[x, y]]);
    touch("touchmove", [[100, 400]]);
    touch("touchend", []);
    expect(indicator()).toBeNull();
    expect(window.reloadPage).not.toHaveBeenCalled();
  });

  test("a second finger during a pull hides the indicator and cancels", () => {
    run();
    pull([200]);
    touch("touchmove", [[100, 300], [150, 300]]);
    expect(indicator().style.opacity).toBe("0");
    touch("touchend", []);
    expect(window.reloadPage).not.toHaveBeenCalled();
  });

  test("the page scrolling during a pull cancels it", () => {
    run();
    pull([200]);
    window.scrollY = 5;
    touch("touchmove", [[100, 320]]);
    touch("touchend", []);
    expect(window.reloadPage).not.toHaveBeenCalled();
  });

  test("touchcancel hides the indicator, with or without one on the page", () => {
    run();
    expect(() => touch("touchcancel", [])).not.toThrow();
    pull([200]);
    touch("touchcancel", []);
    expect(indicator().style.opacity).toBe("0");
    touch("touchend", []);
    expect(window.reloadPage).not.toHaveBeenCalled();
  });

  test("no second pull while a refresh is under way", () => {
    run();
    pull([200]);
    touch("touchend", []);
    pull([200]);
    touch("touchend", []);
    expect(window.reloadPage).toHaveBeenCalledTimes(1);
  });

  test("returning from the back-forward cache clears the spinner and allows a new pull", () => {
    run();
    window.dispatchEvent(new Event("pageshow"));
    pull([200]);
    touch("touchend", []);
    window.dispatchEvent(new Event("pageshow"));
    const el = indicator();
    expect(el.classList.contains("spinning")).toBe(false);
    expect(el.style.opacity).toBe("0");
    pull([200]);
    touch("touchend", []);
    expect(window.reloadPage).toHaveBeenCalledTimes(2);
  });
});
