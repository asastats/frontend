/**
 * @jest-environment jsdom
 */

/**
 * Wiring for the connected-addresses manager.
 *
 * Everything here is a branch that decides *whether a signature is demanded*
 * or *whether a failure is shown*, so the cases below are mostly the paths
 * where one of those quietly does not happen: a click that is not a step-up
 * button, a CSRF token that is only in the DOM, an htmx that never loaded.
 *
 * `runStepUp` and `buildStepUpSign` are mocked out — they have their own
 * suites, and what is under test here is which of them gets called with what.
 */

const runStepUpMock = jest.fn();
jest.mock("./manageBridge", () => ({
  runStepUp: (...args: unknown[]) => runStepUpMock(...args),
}));

const buildStepUpSignMock = jest.fn(() => "SIGNER");
jest.mock("./manageAdapters", () => ({
  buildStepUpSign: (...args: unknown[]) => buildStepUpSignMock(...args),
}));

const notifyMock = jest.fn();
jest.mock("./notify", () => ({
  notify: (...args: unknown[]) => notifyMock(...args),
}));

import { initManageAddresses } from "./manageBootstrap";

/** Render the container with one step-up button and one plain htmx button. */
function render(attrs = ""): HTMLElement {
  document.body.innerHTML = `
    <div id="connected-addresses" ${attrs}>
      <button id="stepup" data-stepup data-operation="set_login"
              data-target-id="7" data-enabled="true">
        <span id="inner">Enable</span>
      </button>
      <button id="plain" hx-post="/remove/">Remove</button>
    </div>`;
  return document.getElementById("connected-addresses") as HTMLElement;
}

beforeEach(() => {
  jest.clearAllMocks();
  document.body.innerHTML = "";
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  runStepUpMock.mockResolvedValue(undefined);
  delete (window as any).htmx;
});

describe("initManageAddresses gating", () => {
  it("no-ops when the container is absent", () => {
    document.body.innerHTML = `<div></div>`;
    initManageAddresses();
    expect(buildStepUpSignMock).not.toHaveBeenCalled();
  });

  it("builds the signer from the container's data attributes", () => {
    render('data-api-base="/api/v2/custom" data-wc-project-id="pid-9"');
    initManageAddresses();
    expect(buildStepUpSignMock).toHaveBeenCalledWith({
      apiBase: "/api/v2/custom",
      wcProjectId: "pid-9",
    });
  });

  it("falls back to the default API base and an empty project id", () => {
    render();
    initManageAddresses();
    expect(buildStepUpSignMock).toHaveBeenCalledWith({
      apiBase: "/api/v2/wallet",
      wcProjectId: "",
    });
  });
});

describe("clicks", () => {
  it("ignores a click that is not on a step-up button", () => {
    render();
    initManageAddresses();
    document.getElementById("plain")!.click();
    expect(runStepUpMock).not.toHaveBeenCalled();
  });

  it("intercepts a step-up click and forwards the button's dataset", () => {
    render();
    initManageAddresses();
    document.getElementById("stepup")!.click();

    expect(runStepUpMock).toHaveBeenCalledTimes(1);
    const [operation, deps] = runStepUpMock.mock.calls[0];
    expect(operation).toEqual({
      operation: "set_login",
      targetId: 7,
      enabled: true,
    });
    expect(deps.stepUpSign).toBe("SIGNER");
    expect(deps.apiBase).toBe("/api/v2/wallet");
  });

  it("finds the button from a click on a child element", () => {
    // `closest` is what makes the span inside the button work; a naive
    // `event.target` check would ignore the most likely click of all.
    render();
    initManageAddresses();
    document.getElementById("inner")!.click();
    expect(runStepUpMock).toHaveBeenCalledTimes(1);
  });

  it("prevents the default action so htmx does not also post", () => {
    render();
    initManageAddresses();
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    document.getElementById("stepup")!.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  });

  it("defaults a button with no dataset to empty operation and NaN target", () => {
    document.body.innerHTML = `
      <div id="connected-addresses"><button id="bare" data-stepup></button></div>`;
    initManageAddresses();
    document.getElementById("bare")!.click();
    const [operation] = runStepUpMock.mock.calls[0];
    expect(operation.operation).toBe("");
    expect(operation.targetId).toBeNaN();
    expect(operation.enabled).toBe(false);
  });
});

describe("the CSRF token", () => {
  it("prefers the cookie", () => {
    document.cookie = "csrftoken=from-cookie";
    render();
    initManageAddresses();
    document.getElementById("stepup")!.click();
    expect(runStepUpMock.mock.calls[0][1].csrf).toBe("from-cookie");
  });

  it("falls back to the hidden input when there is no cookie", () => {
    render();
    document.body.insertAdjacentHTML(
      "beforeend",
      '<input name="csrfmiddlewaretoken" value="from-input">'
    );
    initManageAddresses();
    document.getElementById("stepup")!.click();
    expect(runStepUpMock.mock.calls[0][1].csrf).toBe("from-input");
  });

  it("is an empty string when neither is present", () => {
    render();
    initManageAddresses();
    document.getElementById("stepup")!.click();
    expect(runStepUpMock.mock.calls[0][1].csrf).toBe("");
  });
});

describe("the htmx ajax callback", () => {
  /** Run one click and return the `ajax` function handed to runStepUp. */
  function ajaxCallback() {
    render();
    initManageAddresses();
    document.getElementById("stepup")!.click();
    return runStepUpMock.mock.calls[0][1].ajax;
  }

  it("rejects when htmx never loaded", async () => {
    // Resolved per click rather than at init, because htmx may load after
    // this bundle does.
    await expect(ajaxCallback()("/ops/", { a: 1 })).rejects.toThrow(
      "htmx is not loaded on this page"
    );
  });

  it("rejects when htmx is present but has no ajax", async () => {
    const ajax = ajaxCallback();
    (window as any).htmx = {};
    await expect(ajax("/ops/", {})).rejects.toThrow("htmx is not loaded");
  });

  it("posts through htmx, swapping the list in place", async () => {
    const htmxAjax = jest.fn().mockResolvedValue(undefined);
    const ajax = ajaxCallback();
    (window as any).htmx = { ajax: htmxAjax };

    await ajax("/ops/", { nonce: "n" });

    expect(htmxAjax).toHaveBeenCalledWith("POST", "/ops/", {
      target: "#connected-addresses-list",
      swap: "innerHTML",
      source: document.getElementById("connected-addresses"),
      values: { nonce: "n" },
    });
  });
});

describe("failures reach the reader", () => {
  it("toasts the message when runStepUp rejects with an Error", async () => {
    runStepUpMock.mockRejectedValue(new Error("user rejected"));
    render();
    initManageAddresses();
    document.getElementById("stepup")!.click();
    await Promise.resolve();
    await Promise.resolve();
    expect(notifyMock).toHaveBeenCalledWith(null, "user rejected");
  });

  it("stringifies a rejection that is not an Error", async () => {
    runStepUpMock.mockRejectedValue("plain string");
    render();
    initManageAddresses();
    document.getElementById("stepup")!.click();
    await Promise.resolve();
    await Promise.resolve();
    expect(notifyMock).toHaveBeenCalledWith(null, "plain string");
  });

  it("shows a server-signalled wallet-error carrying a detail value", () => {
    render();
    initManageAddresses();
    document.body.dispatchEvent(
      new CustomEvent("wallet-error", { detail: { value: "address in use" } })
    );
    expect(notifyMock).toHaveBeenCalledWith(null, "address in use");
  });

  it("shows a wallet-error whose detail is a bare string", () => {
    render();
    initManageAddresses();
    document.body.dispatchEvent(
      new CustomEvent("wallet-error", { detail: "went wrong" })
    );
    expect(notifyMock).toHaveBeenCalledWith(null, "went wrong");
  });

  it("falls back to a generic message when the detail says nothing", () => {
    render();
    initManageAddresses();
    document.body.dispatchEvent(new CustomEvent("wallet-error", { detail: {} }));
    expect(notifyMock).toHaveBeenCalledWith(null, "Operation failed");
  });

  it("falls back when there is no detail at all", () => {
    render();
    initManageAddresses();
    document.body.dispatchEvent(new CustomEvent("wallet-error"));
    expect(notifyMock).toHaveBeenCalledWith(null, "Operation failed");
  });
});
