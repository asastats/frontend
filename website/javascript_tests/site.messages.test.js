/**
 * `initMessageToasts` -- the dismiss button and the auto-hide.
 *
 * The toasts themselves are rendered by `snippets/messages.html` on the
 * server, so a message is readable with scripting off. What is tested here is
 * only what needs a script, and the hover/focus reprieve, which exists because
 * eight seconds is a guess about reading speed and is wrong for anyone who
 * reads slowly or looked away.
 */
const jquery = require("../static/js/jquery-2.2.4.min.js");

window.$ = jquery;
$.prototype.sidenav = jest.fn();
$.prototype.modal = jest.fn();

const site = require("../static/js/site.js");

/** The markup `snippets/messages.html` emits for one non-error message. */
const toast = (body) =>
  '<div class="toast toast-center toast-bottom z-50" data-message-toasts>' +
  '  <div class="alert alert-success shadow-lg" role="status" data-message-toast>' +
  "    <span>" +
  body +
  "</span>" +
  '    <button type="button" data-dismiss-toast aria-label="Dismiss this message">x</button>' +
  "  </div>" +
  "</div>";

beforeEach(() => {
  document.body.innerHTML = toast("Layout preference saved.");
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
  jest.resetModules();
});

describe("initMessageToasts", function () {
  test("the close button removes the toast", function () {
    site.initMessageToasts();
    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(1);

    document.querySelector("[data-dismiss-toast]").click();

    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(0);
  });

  test("a toast hides itself once the timer runs out", function () {
    site.initMessageToasts();

    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS - 1);
    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(1);

    jest.advanceTimersByTime(1);
    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(0);
  });

  test("hovering stops the clock, and it stays while the pointer is on it", function () {
    site.initMessageToasts();
    const element = document.querySelector("[data-message-toast]");

    element.dispatchEvent(new Event("mouseenter"));
    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS * 3);

    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(1);
  });

  test("leaving restarts the clock rather than leaving it stopped", function () {
    site.initMessageToasts();
    const element = document.querySelector("[data-message-toast]");

    element.dispatchEvent(new Event("mouseenter"));
    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS * 2);
    element.dispatchEvent(new Event("mouseleave"));
    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS);

    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(0);
  });

  test("keyboard focus earns the same reprieve as the pointer", function () {
    // `focusin` rather than `focus`: the close button is the focusable child
    // and `focus` does not bubble, so a keyboard user tabbing to Dismiss would
    // otherwise have the toast vanish from under them.
    site.initMessageToasts();
    const element = document.querySelector("[data-message-toast]");

    element.dispatchEvent(new Event("focusin"));
    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS * 3);

    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(1);
  });

  test("dismissing a paused toast does not leave its timer to fire", function () {
    // `remove()` on an element already removed is harmless, so this is about
    // the timer being cleared rather than about a second removal.
    site.initMessageToasts();
    const element = document.querySelector("[data-message-toast]");

    document.querySelector("[data-dismiss-toast]").click();
    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS * 2);

    expect(element.isConnected).toBe(false);
  });

  test("hovering and then clicking the close button works", function () {
    // The ordinary way a toast is dismissed: the pointer arrives, which stops
    // the clock, and the click lands with no timer left to clear.
    site.initMessageToasts();
    const element = document.querySelector("[data-message-toast]");

    element.dispatchEvent(new Event("mouseenter"));
    document.querySelector("[data-dismiss-toast]").click();

    expect(element.isConnected).toBe(false);
  });

  test("a toast with no close button still hides itself", function () {
    // The button is rendered by the template, so its absence means someone
    // changed the markup. The timer must not depend on it.
    document.body.innerHTML = toast("Saved").replace(
      /<button[\s\S]*?<\/button>/,
      ""
    );
    site.initMessageToasts();
    expect(document.querySelector("[data-dismiss-toast]")).toBeNull();

    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS);

    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(0);
  });

  test("a second hover while already paused does not restart anything", function () {
    // `mouseenter` twice with no `mouseleave` between: the second finds the
    // timer already cleared. Real pointers generate this, and so does a
    // `focusin` arriving while the pointer is still resting on the toast.
    site.initMessageToasts();
    const element = document.querySelector("[data-message-toast]");

    element.dispatchEvent(new Event("mouseenter"));
    element.dispatchEvent(new Event("mouseenter"));
    element.dispatchEvent(new Event("focusin"));
    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS * 3);

    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(1);
  });

  test("wiring twice does not give a toast two timers", function () {
    // htmx swaps run this again, and an untouched toast would otherwise
    // collect a second set of listeners and a second timer. Two timers means
    // the hover reprieve stops working: only one of them is ever cleared, so
    // the toast vanishes from under a reader who is holding it open.
    site.initMessageToasts();
    site.initMessageToasts();
    const element = document.querySelector("[data-message-toast]");

    element.dispatchEvent(new Event("mouseenter"));
    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS * 3);

    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(1);
  });

  test("a toast swapped in later gets wired too", function () {
    site.initMessageToasts();
    document.body.insertAdjacentHTML("beforeend", toast("Explorer preference saved."));
    site.initMessageToasts();

    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(2);
    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS);

    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(0);
  });

  test("a page with no toasts is not an error", function () {
    document.body.innerHTML = "<p>nothing to announce</p>";
    expect(() => site.initMessageToasts()).not.toThrow();
  });

  test("every toast on the page gets its own timer", function () {
    document.body.innerHTML =
      toast("Layout preference saved.") + toast("Explorer preference saved.");
    site.initMessageToasts();
    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(2);

    // one is held open; the other must still go
    document
      .querySelectorAll("[data-message-toast]")[0]
      .dispatchEvent(new Event("mouseenter"));
    jest.advanceTimersByTime(site.MESSAGE_TOAST_MILLISECONDS);

    expect(document.querySelectorAll("[data-message-toast]")).toHaveLength(1);
  });
});
