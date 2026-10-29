import { webcrypto } from "crypto";

import {
  MESSAGES,
  NATIVE_NONCE_PATH,
  NATIVE_PATH,
  NATIVE_PROVIDERS,
  NativeSignIn,
  REDEEM_PATH,
  RETURN_PATH,
  WebAuth,
  armConnect,
  base64url,
  challengeFor,
  connect,
  fetchNonce,
  installSignIn,
  makeVerifier,
  nativeAvailable,
  nativeSignIn,
  nextFor,
  redeem,
  signIn,
  ticketFrom,
} from "./signIn";

jest.mock("@capacitor/core", () => ({
  registerPlugin: jest.fn(() => ({ start: jest.fn(), isAvailable: jest.fn(), signIn: jest.fn() })),
}));
jest.mock("./push", () => ({ csrfToken: () => "csrf-1" }));

const ORIGIN = "https://www.asastats.com";
const start = WebAuth.start as jest.Mock;
const isAvailable = NativeSignIn.isAvailable as jest.Mock;
const nativeSheet = NativeSignIn.signIn as jest.Mock;
const fetchMock = jest.fn();
const callback = (ticket = "t-1") => `${ORIGIN}${RETURN_PATH}?ticket=${ticket}`;

/** Where `location` points, for `nextFor`. */
const at = (pathname: string, search = "") => ({ pathname, search }) as Location;

let submitted: HTMLFormElement[];

beforeAll(() => {
  Object.defineProperty(globalThis, "crypto", { value: webcrypto, configurable: true });
});

beforeEach(() => {
  Object.assign(window.location, { origin: ORIGIN, pathname: "/", search: "" });
  document.body.innerHTML = "";
  submitted = [];
  jest
    .spyOn(HTMLFormElement.prototype, "submit")
    .mockImplementation(function (this: HTMLFormElement) {
      submitted.push(this);
    });
  start.mockResolvedValue({ url: callback() });
  // The browser flow unless a test arms a native sheet.
  isAvailable.mockResolvedValue({ available: false });
  nativeSheet.mockResolvedValue({ idToken: "id-1" });
  fetchMock.mockResolvedValue({
    ok: true,
    json: async () => ({ nonce: "n-1", google_client_id: "web.apps.googleusercontent.com" }),
  });
  Object.defineProperty(globalThis, "fetch", { value: fetchMock, configurable: true, writable: true });
});

/** The submitted form's fields. */
const fields = (form: HTMLFormElement) =>
  Object.fromEntries(new FormData(form).entries()) as Record<string, string>;

describe("base64url", () => {
  it("drops padding and swaps the url-unsafe characters", () => {
    expect(base64url(new Uint8Array([251, 255, 254]))).toBe("-__-");
    expect(base64url(new Uint8Array([1]))).toBe("AQ");
  });
});

describe("makeVerifier", () => {
  it("is 43 base64url characters and fresh each time", () => {
    const one = makeVerifier();
    expect(one).toMatch(/^[A-Za-z0-9_-]{43}$/);
    expect(makeVerifier()).not.toBe(one);
  });
});

describe("challengeFor", () => {
  it("matches the server's challenge_for (RFC 7636 appendix B)", async () => {
    await expect(challengeFor("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk")).resolves.toBe(
      "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    );
  });
});

describe("nextFor", () => {
  it("prefers the next parameter", () => {
    expect(nextFor(at("/accounts/login/", "?next=/profile/"))).toBe("/profile/");
  });

  it("leaves the sign-in pages to the server's default", () => {
    expect(nextFor(at("/accounts/login/"))).toBeUndefined();
  });

  it("returns to the page the modal was opened on", () => {
    expect(nextFor(at("/ADDR/", "?tab=2"))).toBe("/ADDR/?tab=2");
  });
});

describe("ticketFrom", () => {
  it("reads the ticket from our callback", () => {
    expect(ticketFrom(callback("abc"), ORIGIN)).toBe("abc");
  });

  it.each([
    ["another origin", `https://evil.example${RETURN_PATH}?ticket=abc`],
    ["another path", `${ORIGIN}/elsewhere/?ticket=abc`],
    ["no ticket", `${ORIGIN}${RETURN_PATH}`],
    ["not a URL", "::"],
  ])("refuses %s", (_, url) => {
    expect(ticketFrom(url, ORIGIN)).toBeNull();
  });
});

describe("redeem", () => {
  it("posts ticket, verifier and the CSRF token as a hidden form", () => {
    redeem("t-1", "v-1");

    const [form] = submitted;
    expect(form.method).toBe("post");
    expect(new URL(form.action).pathname).toBe(REDEEM_PATH);
    expect(form.hidden).toBe(true);
    expect(fields(form)).toEqual({ ticket: "t-1", verifier: "v-1", csrfmiddlewaretoken: "csrf-1" });
  });
});

describe("signIn", () => {
  it("starts the sheet with a challenge of the verifier it redeems with", async () => {
    const say = jest.fn();

    await expect(signIn("google", "/profile/", say)).resolves.toBe(true);

    const options = start.mock.calls[0][0];
    expect(options.provider).toBe("google");
    expect(options.next).toBe("/profile/");
    const { ticket, verifier } = fields(submitted[0]);
    expect(ticket).toBe("t-1");
    expect(await challengeFor(verifier)).toBe(options.challenge);
    expect(say).not.toHaveBeenCalled();
  });

  it("defaults next to this page and the message to an alert", async () => {
    Object.assign(window.location, { pathname: "/ADDR/" });

    await signIn("github");

    expect(start.mock.calls[0][0].next).toBe("/ADDR/");
  });

  it.each(["cancelled", "busy"])("stays quiet when the sheet answers %s", async (reason) => {
    start.mockRejectedValue(new Error(reason));
    const say = jest.fn();

    await expect(signIn("google", undefined, say)).resolves.toBe(false);

    expect(say).not.toHaveBeenCalled();
    expect(submitted).toHaveLength(0);
  });

  it("explains an unsupported device", async () => {
    start.mockRejectedValue(new Error("unsupported"));
    const say = jest.fn();

    await signIn("google", undefined, say);

    expect(say).toHaveBeenCalledWith(MESSAGES.unsupported);
  });

  it("reports any other failure", async () => {
    start.mockRejectedValue(undefined);
    const say = jest.fn();

    await signIn("google", undefined, say);

    expect(say).toHaveBeenCalledWith(MESSAGES.failed);
  });

  it("refuses a callback that is not ours", async () => {
    start.mockResolvedValue({ url: "https://evil.example/app/auth/return/?ticket=x" });
    const say = jest.fn();

    await expect(signIn("google", undefined, say)).resolves.toBe(false);

    expect(say).toHaveBeenCalledWith(MESSAGES.failed);
    expect(submitted).toHaveLength(0);
  });

  it("alerts by default", async () => {
    start.mockRejectedValue(new Error("unsupported"));
    const alert = jest.spyOn(window, "alert").mockImplementation(() => undefined);

    await signIn("google");

    expect(alert).toHaveBeenCalledWith(MESSAGES.unsupported);
  });
});

describe("installSignIn", () => {
  beforeAll(() => installSignIn());

  beforeEach(() => {
    document.body.innerHTML =
      '<a href="/accounts/google/login/" data-app-signin="google"><span id="in">G</span></a>' +
      '<a href="/elsewhere/" id="plain">x</a>';
  });

  /** Click `element` and report whether the navigation was prevented. */
  const click = (element: Element, init: MouseEventInit = {}) => {
    const event = new MouseEvent("click", { bubbles: true, cancelable: true, ...init });
    element.dispatchEvent(event);
    return event.defaultPrevented;
  };

  it("signs in instead of following the link", async () => {
    expect(click(document.getElementById("in")!)).toBe(true);
    // The digest before `start` runs on Node's thread pool: one tick is not always enough.
    for (let i = 0; i < 200 && !start.mock.calls.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 5));
    }
    expect(start.mock.calls[0][0].provider).toBe("google");
  });

  it("leaves other links alone", () => {
    expect(click(document.getElementById("plain")!)).toBe(false);
    expect(start).not.toHaveBeenCalled();
  });

  it("leaves a middle click alone", () => {
    expect(click(document.getElementById("in")!, { button: 1 })).toBe(false);
  });

  it("leaves a click another handler took", () => {
    const link = document.getElementById("in")!;
    link.addEventListener("click", (event) => event.preventDefault(), { once: true });
    click(link);
    expect(start).not.toHaveBeenCalled();
  });

  it("ignores events without a target element", () => {
    document.dispatchEvent(new MouseEvent("click"));
    expect(start).not.toHaveBeenCalled();
  });
});

/** Let pending promise callbacks run. */
const settle = () => new Promise((resolve) => setTimeout(resolve, 0));

describe("nativeAvailable", () => {
  it("asks the plugin for Apple and Google only", async () => {
    isAvailable.mockResolvedValue({ available: true });

    await expect(nativeAvailable("google")).resolves.toBe(true);
    await expect(nativeAvailable("github")).resolves.toBe(false);

    expect(NATIVE_PROVIDERS).toEqual(["apple", "google"]);
    expect(isAvailable).toHaveBeenCalledTimes(1);
    expect(isAvailable).toHaveBeenCalledWith({ provider: "google" });
  });

  it("is false for an app without the plugin", async () => {
    isAvailable.mockRejectedValue(new Error("not implemented"));

    await expect(nativeAvailable("apple")).resolves.toBe(false);
  });

  it("is false unless the plugin says true", async () => {
    isAvailable.mockResolvedValue({});

    await expect(nativeAvailable("apple")).resolves.toBe(false);
  });
});

describe("fetchNonce", () => {
  it("posts with the CSRF header and returns the body", async () => {
    await expect(fetchNonce()).resolves.toEqual({
      nonce: "n-1",
      google_client_id: "web.apps.googleusercontent.com",
    });

    expect(fetchMock).toHaveBeenCalledWith(NATIVE_NONCE_PATH, {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-CSRFToken": "csrf-1" },
    });
  });

  it("fails on a refusal", async () => {
    fetchMock.mockResolvedValue({ ok: false });

    await expect(fetchNonce()).rejects.toThrow("failed");
  });
});

describe("nativeSignIn", () => {
  it("posts Apple's token, code and name with the process and next", async () => {
    nativeSheet.mockResolvedValue({
      idToken: "id-a",
      authorizationCode: "c-a",
      givenName: "Ana",
      familyName: "B",
    });
    const say = jest.fn();

    await expect(nativeSignIn("apple", "login", "/profile/", say)).resolves.toBe("sent");

    expect(nativeSheet).toHaveBeenCalledWith({
      provider: "apple",
      nonce: "n-1",
      serverClientId: "web.apps.googleusercontent.com",
    });
    const [form] = submitted;
    expect(new URL(form.action).pathname).toBe(NATIVE_PATH);
    expect(fields(form)).toEqual({
      provider: "apple",
      process: "login",
      id_token: "id-a",
      code: "c-a",
      first_name: "Ana",
      last_name: "B",
      next: "/profile/",
      csrfmiddlewaretoken: "csrf-1",
    });
    expect(say).not.toHaveBeenCalled();
  });

  it("sends only the token for Google, and no next when connecting", async () => {
    await nativeSignIn("google", "connect", "/profile/", jest.fn());

    expect(fields(submitted[0])).toEqual({
      provider: "google",
      process: "connect",
      id_token: "id-1",
      csrfmiddlewaretoken: "csrf-1",
    });
  });

  it("falls back when the phone has no account for the sheet", async () => {
    nativeSheet.mockRejectedValue(new Error("unavailable"));
    const say = jest.fn();

    await expect(nativeSignIn("google", "login", undefined, say)).resolves.toBe("fallback");

    expect(say).not.toHaveBeenCalled();
    expect(submitted).toHaveLength(0);
  });

  it.each(["cancelled", "busy"])("stays quiet when the sheet answers %s", async (reason) => {
    nativeSheet.mockRejectedValue(new Error(reason));
    const say = jest.fn();

    await expect(nativeSignIn("google", "login", undefined, say)).resolves.toBe("stopped");

    expect(say).not.toHaveBeenCalled();
  });

  it("reports a refused nonce or any other failure", async () => {
    fetchMock.mockResolvedValue({ ok: false });
    const say = jest.fn();

    await expect(nativeSignIn("google", "login", undefined, say)).resolves.toBe("stopped");
    nativeSheet.mockRejectedValue(undefined);
    fetchMock.mockResolvedValue({ ok: true, json: async () => ({ nonce: "n" }) });
    await nativeSignIn("google", "login", undefined, say);

    expect(say).toHaveBeenCalledTimes(2);
    expect(say).toHaveBeenCalledWith(MESSAGES.failed);
    expect(submitted).toHaveLength(0);
  });
});

describe("signIn with a native sheet", () => {
  beforeEach(() => isAvailable.mockResolvedValue({ available: true }));

  it("uses the sheet and not the browser", async () => {
    await expect(signIn("google", "/profile/", jest.fn())).resolves.toBe(true);

    expect(start).not.toHaveBeenCalled();
    expect(fields(submitted[0]).next).toBe("/profile/");
  });

  it("reports false when the sheet is cancelled", async () => {
    nativeSheet.mockRejectedValue(new Error("cancelled"));

    await expect(signIn("google", undefined, jest.fn())).resolves.toBe(false);

    expect(start).not.toHaveBeenCalled();
  });

  it("falls back to the browser without an account on the phone", async () => {
    nativeSheet.mockRejectedValue(new Error("unavailable"));

    await expect(signIn("google", "/profile/", jest.fn())).resolves.toBe(true);

    expect(start).toHaveBeenCalled();
    expect(new URL(submitted[0].action).pathname).toBe(REDEEM_PATH);
  });
});

describe("connect", () => {
  it("connects with the sheet", async () => {
    const say = jest.fn();

    await expect(connect("google", say)).resolves.toBe(true);

    expect(fields(submitted[0]).process).toBe("connect");
    expect(say).not.toHaveBeenCalled();
  });

  it("points to the website without an account on the phone", async () => {
    nativeSheet.mockRejectedValue(new Error("unavailable"));
    const alert = jest.spyOn(window, "alert").mockImplementation(() => undefined);

    await expect(connect("google")).resolves.toBe(false);

    expect(alert).toHaveBeenCalledWith(MESSAGES.connectOnWebsite);
  });
});

describe("armConnect", () => {
  beforeEach(() => {
    document.body.innerHTML =
      '<a href="/accounts/google/login/?process=connect" id="g" data-app-connect="google" hidden>G</a>' +
      '<p id="note" data-app-connect-fallback="google">Website</p>' +
      '<a href="/accounts/apple/login/?process=connect" id="a" data-app-connect="apple">A</a>';
  });

  it("shows the buttons this phone has a sheet for and hides their note", async () => {
    isAvailable.mockImplementation(async ({ provider }) => ({ available: provider === "google" }));

    await armConnect();

    const google = document.getElementById("g")!;
    expect(google.hidden).toBe(false);
    expect(google.dataset.appConnectReady).toBe("");
    expect(document.getElementById("note")!.hidden).toBe(true);
    expect(document.getElementById("a")!.dataset.appConnectReady).toBeUndefined();
  });

  it("leaves everything as served without the plugin", async () => {
    await armConnect();

    expect(document.getElementById("g")!.hidden).toBe(true);
    expect(document.getElementById("note")!.hidden).toBe(false);
  });
});

describe("installSignIn on the Connections page", () => {
  /** A fresh document, so the earlier suites' listener does not answer too. */
  let doc: Document;

  beforeEach(() => {
    doc = document.implementation.createHTMLDocument("connections");
    doc.body.innerHTML =
      '<a href="/accounts/apple/login/?process=connect" data-app-connect="apple"><span id="apple">A</span></a>';
  });

  const click = (element: Element) => {
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    element.dispatchEvent(event);
    return event.defaultPrevented;
  };

  it("connects through an armed button", async () => {
    isAvailable.mockResolvedValue({ available: true });
    installSignIn(doc);
    await settle();

    expect(click(doc.getElementById("apple")!)).toBe(true);
    await settle();

    expect(nativeSheet.mock.calls[0][0].provider).toBe("apple");
    expect(fields(submitted[0]).process).toBe("connect");
  });

  it("follows the link where the phone has no sheet", async () => {
    installSignIn(doc);
    await settle();

    expect(click(doc.getElementById("apple")!)).toBe(false);
    expect(nativeSheet).not.toHaveBeenCalled();
  });
});
