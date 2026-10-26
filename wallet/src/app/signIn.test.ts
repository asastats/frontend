import { webcrypto } from "crypto";

import {
  MESSAGES,
  REDEEM_PATH,
  RETURN_PATH,
  WebAuth,
  base64url,
  challengeFor,
  installSignIn,
  makeVerifier,
  nextFor,
  redeem,
  signIn,
  ticketFrom,
} from "./signIn";

jest.mock("@capacitor/core", () => ({
  registerPlugin: jest.fn(() => ({ start: jest.fn() })),
}));
jest.mock("./push", () => ({ csrfToken: () => "csrf-1" }));

const ORIGIN = "https://www.asastats.com";
const start = WebAuth.start as jest.Mock;
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
    await new Promise((resolve) => setTimeout(resolve, 0));
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
