import { App } from "@capacitor/app";

import { RETURN_KEY } from "./returnPage";
import {
  ALIVE_KEY,
  HANDOFF_FOR_MS,
  HANDOFF_KEY,
  NOTICE_KEY,
  forgetHandoff,
  handoffTarget,
  handoffWallet,
  installHandoff,
  rememberHandoff,
  showHandoffNotice,
  type HandoffWindow,
} from "./walletHandoff";

jest.mock("@capacitor/app", () => ({
  App: { addListener: jest.fn().mockResolvedValue({ remove: jest.fn() }) },
}));

const ORIGIN = "https://www.asastats.com";
const LOGIN = `${ORIGIN}/accounts/login/`;
const NOW = 1_800_000_000_000;
const PERA = { id: "pera", name: "Pera Wallet" };

/** A wallet card as wallet_signing.html renders it. */
function card(id = "pera", title = "Pera Wallet"): HTMLElement {
  document.body.innerHTML = `
    <main><div id="wallet-${id}" class="card"><div class="card-body">
      <h4 class="card-title"> ${title} </h4>
      <button id="connect-button-${id}"><span>Connect</span></button>
      <button id="auth-button-${id}">Sign in</button>
      <button id="disconnect-button-${id}">Disconnect</button>
    </div></div></main>`;
  return document.getElementById(`wallet-${id}`)!;
}

/** Make an element report a box, as a laid-out one does (jsdom lays out nothing). */
function visible(element: HTMLElement): void {
  element.getClientRects = () => [{}] as unknown as DOMRectList;
}

function noted(value: unknown): void {
  localStorage.setItem(HANDOFF_KEY, typeof value === "string" ? value : JSON.stringify(value));
}

function page(href: string): HandoffWindow & { location: { replace: jest.Mock } } {
  const url = new URL(href);
  return {
    localStorage,
    sessionStorage,
    document,
    location: { href: url.href, origin: url.origin, replace: jest.fn() },
  };
}

/** A storage whose every call throws, as a blocked one does. */
const blocked = {
  getItem: () => {
    throw new Error("blocked");
  },
  setItem: () => {
    throw new Error("blocked");
  },
  removeItem: () => {
    throw new Error("blocked");
  },
} as unknown as Storage;

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  document.body.innerHTML = "";
  (App.addListener as jest.Mock).mockClear();
});

describe("handoffWallet", () => {
  it.each(["connect-button-pera", "auth-button-pera"])("names the wallet behind #%s", (id) => {
    card();
    expect(handoffWallet(document.getElementById(id))).toEqual(PERA);
  });

  it("finds the button from a child of it", () => {
    card();
    expect(handoffWallet(document.querySelector("#connect-button-pera span"))).toEqual(PERA);
  });

  it("falls back to a generic name without a card", () => {
    document.body.innerHTML = '<button id="connect-button-defly">Connect</button>';
    expect(handoffWallet(document.getElementById("connect-button-defly"))).toEqual({
      id: "defly",
      name: "your wallet",
    });
  });

  it.each([
    ["another button", () => document.getElementById("disconnect-button-pera")],
    ["no element", () => null],
    ["a non-element target", () => window],
  ])("ignores %s", (_, target) => {
    card();
    expect(handoffWallet(target() as EventTarget | null)).toBeNull();
  });
});

describe("remember and forget", () => {
  it("keeps the wallet, the page and the time", () => {
    rememberHandoff(PERA, LOGIN, localStorage, NOW);
    expect(JSON.parse(localStorage.getItem(HANDOFF_KEY)!)).toEqual({ ...PERA, url: LOGIN, at: NOW });
    forgetHandoff(localStorage);
    expect(localStorage.getItem(HANDOFF_KEY)).toBeNull();
  });

  it("does not throw on a blocked storage", () => {
    expect(() => rememberHandoff(PERA, LOGIN, blocked, NOW)).not.toThrow();
    expect(() => forgetHandoff(blocked)).not.toThrow();
  });
});

describe("handoffTarget", () => {
  const target = () => handoffTarget(localStorage, sessionStorage, ORIGIN, NOW);

  it("returns the lost step after a restart, once", () => {
    noted({ ...PERA, url: LOGIN, at: NOW - 60_000 });
    expect(target()).toEqual({ ...PERA, url: LOGIN });
    expect(localStorage.getItem(HANDOFF_KEY)).toBeNull();
    expect(sessionStorage.getItem(ALIVE_KEY)).toBe("1");
  });

  it("ignores it on a page change in the same WebView, and drops it", () => {
    sessionStorage.setItem(ALIVE_KEY, "1");
    noted({ ...PERA, url: LOGIN, at: NOW });
    expect(target()).toBeNull();
    expect(localStorage.getItem(HANDOFF_KEY)).toBeNull();
  });

  it.each([
    ["nothing noted", null],
    ["not JSON", "{"],
    ["no wallet id", { name: "Pera Wallet", url: LOGIN, at: NOW }],
    ["no wallet name", { id: "pera", url: LOGIN, at: NOW }],
    ["no page", { ...PERA, at: NOW }],
    ["no time", { ...PERA, url: LOGIN }],
    ["too old", { ...PERA, url: LOGIN, at: NOW - HANDOFF_FOR_MS - 1 }],
    ["in the future", { ...PERA, url: LOGIN, at: NOW + 1 }],
    ["another site", { ...PERA, url: "https://example.com/", at: NOW }],
    ["not a URL", { ...PERA, url: "::", at: NOW }],
  ])("returns null for %s", (_, value) => {
    if (value !== null) noted(value);
    expect(target()).toBeNull();
  });

  it("returns null on a blocked storage", () => {
    expect(handoffTarget(blocked, sessionStorage, ORIGIN, NOW)).toBeNull();
  });
});

describe("showHandoffNotice", () => {
  it("explains it in the visible wallet card", () => {
    const element = card();
    visible(element);
    const notice = showHandoffNotice(document, PERA)!;
    expect(notice.parentElement).toBe(element);
    expect(notice.dataset.notice).toBe("info");
    expect(notice.getAttribute("role")).toBe("status");
    expect(notice.textContent).toBe(
      "Your phone closed ASA Stats while Pera Wallet was open, so that step did not finish. " +
        "Please connect again."
    );
  });

  it("goes to the top of the page when the card is hidden (the login modal)", () => {
    card();
    const notice = showHandoffNotice(document, PERA)!;
    expect(document.querySelector("main")!.firstElementChild).toBe(notice);
  });

  it("shows nothing on a page without a place for it", () => {
    expect(showHandoffNotice(document, PERA)).toBeNull();
  });

  it("renders the wallet name as text", () => {
    document.body.innerHTML = "<main></main>";
    const notice = showHandoffNotice(document, { id: "x", name: "<b>x</b>" })!;
    expect(notice.querySelector("b")).toBeNull();
  });
});

describe("installHandoff", () => {
  it("notes a tap on Connect and forgets it on resume", async () => {
    card();
    const win = page(LOGIN);
    expect(installHandoff(win, NOW)).toBe(false);
    document.getElementById("connect-button-pera")!.click();
    expect(JSON.parse(localStorage.getItem(HANDOFF_KEY)!)).toMatchObject({ ...PERA, url: LOGIN });

    const [event, listener] = (App.addListener as jest.Mock).mock.calls[0];
    expect(event).toBe("resume");
    listener();
    expect(localStorage.getItem(HANDOFF_KEY)).toBeNull();
  });

  it("defaults to this window and the current time", () => {
    expect(installHandoff()).toBe(false);
    expect(sessionStorage.getItem(ALIVE_KEY)).toBe("1");
  });

  it("notes nothing for other clicks", () => {
    card();
    installHandoff(page(LOGIN), NOW);
    document.getElementById("disconnect-button-pera")!.click();
    expect(localStorage.getItem(HANDOFF_KEY)).toBeNull();
  });

  it("goes back to the wallet's page after a restart and explains there", () => {
    noted({ ...PERA, url: LOGIN, at: NOW });
    localStorage.setItem(RETURN_KEY, JSON.stringify({ url: `${ORIGIN}/faq/`, at: NOW }));
    const start = page(`${ORIGIN}/`);
    expect(installHandoff(start, NOW)).toBe(true);
    expect(start.location.replace).toHaveBeenCalledWith(LOGIN);
    expect(localStorage.getItem(RETURN_KEY)).toBeNull();

    visible(card());
    expect(installHandoff(page(LOGIN), NOW)).toBe(false);
    expect(document.querySelector("[data-notice]")!.textContent).toContain("Pera Wallet");
    expect(localStorage.getItem(NOTICE_KEY)).toBeNull();
  });

  it("explains at once when the restart lands on the wallet's page", () => {
    visible(card());
    noted({ ...PERA, url: LOGIN, at: NOW });
    const start = page(LOGIN);
    expect(installHandoff(start, NOW)).toBe(false);
    expect(start.location.replace).not.toHaveBeenCalled();
    expect(document.querySelector("[data-notice]")).not.toBeNull();
  });

  it("stays put without a lost step", () => {
    card();
    const start = page(`${ORIGIN}/`);
    expect(installHandoff(start, NOW)).toBe(false);
    expect(start.location.replace).not.toHaveBeenCalled();
    expect(document.querySelector("[data-notice]")).toBeNull();
  });

  it("ignores a malformed pending notice", () => {
    card();
    localStorage.setItem(NOTICE_KEY, '{"id": 1}');
    installHandoff(page(LOGIN), NOW);
    expect(document.querySelector("[data-notice]")).toBeNull();

    localStorage.setItem(NOTICE_KEY, "{");
    installHandoff(page(LOGIN), NOW);
    expect(document.querySelector("[data-notice]")).toBeNull();
  });

  it("stays put when it cannot keep the notice for the next page", () => {
    noted({ ...PERA, url: LOGIN, at: NOW });
    const start = page(`${ORIGIN}/`);
    const setItem = jest.spyOn(Storage.prototype, "setItem").mockImplementation(function (
      this: Storage,
      key: string
    ) {
      if (key === NOTICE_KEY) throw new Error("full");
    });
    expect(installHandoff(start, NOW)).toBe(false);
    setItem.mockRestore();
    expect(start.location.replace).not.toHaveBeenCalled();
  });
});
