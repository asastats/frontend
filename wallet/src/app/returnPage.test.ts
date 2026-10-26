import { App } from "@capacitor/app";
import { Browser } from "@capacitor/browser";

import {
  RETURN_FOR_MS,
  RETURN_KEY,
  forgetReturn,
  installReturn,
  rememberReturn,
  returnTarget,
  type ReturnWindow,
} from "./returnPage";

jest.mock("@capacitor/app", () => ({
  App: { addListener: jest.fn().mockResolvedValue({ remove: jest.fn() }) },
}));
jest.mock("@capacitor/browser", () => ({
  Browser: { addListener: jest.fn().mockResolvedValue({ remove: jest.fn() }) },
}));

const ORIGIN = "https://www.asastats.com";
const PAGE = `${ORIGIN}/2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU`;
const NOW = 1_800_000_000_000;

function at(href: string): ReturnWindow["location"] {
  const url = new URL(href);
  return {
    href: url.href,
    origin: url.origin,
    pathname: url.pathname,
    search: url.search,
    replace: jest.fn(),
  };
}

function saved(value: unknown): Storage {
  localStorage.clear();
  localStorage.setItem(RETURN_KEY, typeof value === "string" ? value : JSON.stringify(value));
  return localStorage;
}

function throwing(): Storage {
  return {
    getItem: () => null,
    setItem: () => {
      throw new Error("QuotaExceededError");
    },
    removeItem: () => {
      throw new Error("SecurityError");
    },
  } as unknown as Storage;
}

beforeEach(() => {
  localStorage.clear();
  jest.clearAllMocks();
});

describe("rememberReturn and forgetReturn", () => {
  it("keeps the page with the time", () => {
    rememberReturn(PAGE, localStorage, NOW);
    expect(JSON.parse(localStorage.getItem(RETURN_KEY) as string)).toEqual({ url: PAGE, at: NOW });
    forgetReturn(localStorage);
    expect(localStorage.getItem(RETURN_KEY)).toBeNull();
  });

  it("defaults to the window's storage and clock", () => {
    rememberReturn(PAGE);
    expect(JSON.parse(localStorage.getItem(RETURN_KEY) as string).url).toBe(PAGE);
    forgetReturn();
    expect(localStorage.getItem(RETURN_KEY)).toBeNull();
  });

  it("never throws when storage refuses", () => {
    expect(() => rememberReturn(PAGE, throwing(), NOW)).not.toThrow();
    expect(() => forgetReturn(throwing())).not.toThrow();
  });
});

describe("returnTarget", () => {
  it("goes back from a fresh start at the root", () => {
    const storage = saved({ url: PAGE, at: NOW - 60_000 });
    expect(returnTarget(at(`${ORIGIN}/`), storage, NOW)).toBe(PAGE);
    expect(storage.getItem(RETURN_KEY)).toBeNull();
  });

  it("goes back up to the limit, not after it", () => {
    expect(returnTarget(at(`${ORIGIN}/`), saved({ url: PAGE, at: NOW - RETURN_FOR_MS }), NOW)).toBe(
      PAGE
    );
    expect(
      returnTarget(at(`${ORIGIN}/`), saved({ url: PAGE, at: NOW - RETURN_FOR_MS - 1 }), NOW)
    ).toBeNull();
  });

  it("does not trust a time in the future", () => {
    expect(returnTarget(at(`${ORIGIN}/`), saved({ url: PAGE, at: NOW + 1 }), NOW)).toBeNull();
  });

  it.each([`${ORIGIN}/faq/`, `${ORIGIN}/?x=1`])("stays on %s and still forgets", (here) => {
    const storage = saved({ url: PAGE, at: NOW });
    expect(returnTarget(at(here), storage, NOW)).toBeNull();
    expect(storage.getItem(RETURN_KEY)).toBeNull();
  });

  it.each([
    ["nothing kept", null],
    ["not JSON", "{"],
    ["no url", { at: NOW }],
    ["no time", { url: PAGE }],
    ["an unparseable url", { url: "http://[bad", at: NOW }],
    ["another site", { url: "https://evil.example/", at: NOW }],
    ["the root itself", { url: `${ORIGIN}/`, at: NOW }],
  ])("stays with %s", (_name, value) => {
    const storage = value === null ? localStorage : saved(value);
    expect(returnTarget(at(`${ORIGIN}/`), storage, NOW)).toBeNull();
  });
});

describe("installReturn", () => {
  function listener(mock: jest.Mock, event: string): () => void {
    const call = mock.mock.calls.find(([name]) => name === event);
    return call[1];
  }

  it("replaces the root with the remembered page", () => {
    saved({ url: PAGE, at: NOW });
    const location = at(`${ORIGIN}/`);
    expect(installReturn({ location, localStorage }, NOW)).toBe(true);
    expect(location.replace).toHaveBeenCalledWith(PAGE);
  });

  it("forgets the page when the app comes back by itself", () => {
    const location = at(PAGE);
    expect(installReturn({ location, localStorage }, NOW)).toBe(false);
    expect(location.replace).not.toHaveBeenCalled();

    for (const [mock, event] of [
      [App.addListener, "resume"],
      [Browser.addListener, "browserFinished"],
    ] as const) {
      rememberReturn(PAGE, localStorage, NOW);
      listener(mock as jest.Mock, event)();
      expect(localStorage.getItem(RETURN_KEY)).toBeNull();
    }
  });

  it("defaults to the window and the clock", () => {
    expect(installReturn()).toBe(false);
  });
});
