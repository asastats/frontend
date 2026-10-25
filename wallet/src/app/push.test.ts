import { App } from "@capacitor/app";

import {
  FirebaseMessaging,
  LOGOUT_PATH,
  MESSAGES,
  STORAGE_KEY,
  checkPush,
  csrfToken,
  disablePush,
  enablePush,
  installPush,
  isLogout,
  register,
  sameOriginUrl,
  storedUrls,
} from "./push";

jest.mock("@capacitor/core", () => ({
  Capacitor: { getPlatform: jest.fn().mockReturnValue("android") },
  registerPlugin: jest.fn(() => ({
    checkPermissions: jest.fn(),
    requestPermissions: jest.fn(),
    getToken: jest.fn(),
    deleteToken: jest.fn(),
    addListener: jest.fn().mockResolvedValue({ remove: jest.fn() }),
  })),
}));
jest.mock("@capacitor/app", () => ({
  App: { getInfo: jest.fn().mockResolvedValue({ version: "1.1.0" }) },
}));

const ORIGIN = "https://www.asastats.com";
const URLS = {
  register: "/widgets/alerts/device/register",
  unregister: "/widgets/alerts/device/unregister",
};
const plugin = FirebaseMessaging as unknown as Record<string, jest.Mock>;
const fetchMock = () => global.fetch as jest.Mock;

/** Answer the permission calls with `receive` and getToken with `token`. */
function firebase(receive = "granted", token = "fcm-1"): void {
  plugin.requestPermissions.mockResolvedValue({ receive });
  plugin.checkPermissions.mockResolvedValue({ receive });
  plugin.getToken.mockResolvedValue({ token });
  plugin.deleteToken.mockResolvedValue(undefined);
}

/** The JSON body of the n-th fetch call. */
const posted = (n = 0) => JSON.parse(fetchMock().mock.calls[n][1].body);

/** Let queued promise callbacks run. */
const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

beforeEach(() => {
  Object.assign(window.location, { origin: ORIGIN, assign: jest.fn() });
  localStorage.clear();
  document.cookie = "csrftoken=abc";
  fetchMock().mockResolvedValue({ ok: true });
  firebase();
});

describe("storedUrls", () => {
  it("is null before the device was turned on", () => {
    expect(storedUrls()).toBeNull();
  });

  it("returns what enablePush kept", () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    expect(storedUrls()).toEqual(URLS);
  });

  it.each(["{", JSON.stringify({ register: "/r" })])("ignores %s", (value) => {
    localStorage.setItem(STORAGE_KEY, value);
    expect(storedUrls()).toBeNull();
  });
});

describe("csrfToken", () => {
  it("reads Django's cookie", () => {
    expect(csrfToken()).toBe("abc");
  });

  it("is empty without one", () => {
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    expect(csrfToken()).toBe("");
  });
});

describe("register", () => {
  it("posts the token, platform and app version with the CSRF header", async () => {
    await expect(register(URLS, "fcm-9")).resolves.toBe(true);
    expect(fetchMock()).toHaveBeenCalledWith(
      URLS.register,
      expect.objectContaining({
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": "abc" },
      })
    );
    expect(posted()).toEqual({ token: "fcm-9", platform: "android", app_version: "1.1.0" });
    expect(App.getInfo).toHaveBeenCalled();
  });
});

describe("enablePush", () => {
  it("asks, registers and remembers the urls", async () => {
    await expect(enablePush(URLS)).resolves.toEqual({ ok: true, message: MESSAGES.on });
    expect(plugin.requestPermissions).toHaveBeenCalled();
    expect(posted().token).toBe("fcm-1");
    expect(storedUrls()).toEqual(URLS);
  });

  it("says where to turn it on when refused, and registers nothing", async () => {
    firebase("denied");
    await expect(enablePush(URLS)).resolves.toEqual({ ok: false, message: MESSAGES.denied });
    expect(fetchMock()).not.toHaveBeenCalled();
    expect(storedUrls()).toBeNull();
  });

  it("reports a server that refuses the device", async () => {
    fetchMock().mockResolvedValue({ ok: false });
    await expect(enablePush(URLS)).resolves.toEqual({ ok: false, message: MESSAGES.refused });
    expect(storedUrls()).toBeNull();
  });

  it("reports a failing plugin call with its message", async () => {
    plugin.getToken.mockRejectedValue(new Error("No APNs token."));
    await expect(enablePush(URLS)).resolves.toEqual({ ok: false, message: "No APNs token." });
  });

  it("still says something when the error has no message", async () => {
    plugin.requestPermissions.mockRejectedValue(new Error(""));
    await expect(enablePush(URLS)).resolves.toEqual({ ok: false, message: MESSAGES.failed });
  });
});

describe("checkPush", () => {
  it("re-registers silently when permission is granted", async () => {
    await expect(checkPush(URLS)).resolves.toBe(true);
    expect(plugin.requestPermissions).not.toHaveBeenCalled();
    expect(storedUrls()).toEqual(URLS);
  });

  it("is off without asking when permission is not granted", async () => {
    firebase("prompt");
    await expect(checkPush(URLS)).resolves.toBe(false);
    expect(plugin.getToken).not.toHaveBeenCalled();
  });

  it("is off when the server refuses", async () => {
    fetchMock().mockResolvedValue({ ok: false });
    await expect(checkPush(URLS)).resolves.toBe(false);
    expect(storedUrls()).toBeNull();
  });

  it("is off when the plugin fails", async () => {
    plugin.checkPermissions.mockRejectedValue(new Error("bridge"));
    await expect(checkPush(URLS)).resolves.toBe(false);
  });
});

describe("disablePush", () => {
  it("does nothing for a device never turned on", async () => {
    await disablePush();
    expect(fetchMock()).not.toHaveBeenCalled();
    expect(plugin.deleteToken).not.toHaveBeenCalled();
  });

  it("unregisters the token, deletes it and forgets the urls", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    await disablePush();
    expect(fetchMock().mock.calls[0][0]).toBe(URLS.unregister);
    expect(posted()).toEqual({ token: "fcm-1" });
    expect(plugin.deleteToken).toHaveBeenCalled();
    expect(storedUrls()).toBeNull();
  });

  it("never throws, so a logout goes ahead offline", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    fetchMock().mockRejectedValue(new TypeError("offline"));
    await expect(disablePush()).resolves.toBeUndefined();
    expect(storedUrls()).toBeNull();
  });
});

describe("sameOriginUrl", () => {
  it("resolves a path against the site", () => {
    expect(sameOriginUrl("/ABC/", ORIGIN)).toBe(`${ORIGIN}/ABC/`);
  });

  it.each([`${ORIGIN}/x/`])("keeps an absolute url of the site", (url) => {
    expect(sameOriginUrl(url, ORIGIN)).toBe(url);
  });

  it.each(["https://evil.example/", "", undefined, 42, "http://[::1"])(
    "refuses %p",
    (value) => {
      expect(sameOriginUrl(value, ORIGIN)).toBeNull();
    }
  );
});

describe("isLogout", () => {
  it.each([
    [LOGOUT_PATH, true],
    [`${ORIGIN}${LOGOUT_PATH}`, true],
    ["/accounts/login/", false],
    [`https://evil.example${LOGOUT_PATH}`, false],
  ])("%s is %p", (target, expected) => {
    expect(isLogout(target)).toBe(expected);
  });
});

describe("installPush", () => {
  const navigate = jest.fn();

  /** The listener installPush gave the plugin for `eventName`. */
  const listener = (eventName: string) =>
    plugin.addListener.mock.calls.find((call) => call[0] === eventName)[1];

  beforeEach(() => {
    document.body.innerHTML = `
      <a id="out" href="${ORIGIN}${LOGOUT_PATH}">Log out</a>
      <a id="faq" href="${ORIGIN}/faq/">FAQ</a>
      <span id="plain">text</span>
      <form id="logout" method="post" action="${ORIGIN}${LOGOUT_PATH}"></form>
      <form id="other" method="post" action="/profile/"></form>`;
    installPush(document, navigate);
  });

  it("re-registers a refreshed token for a device that is on", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    listener("tokenReceived")({ token: "fcm-new" });
    await flush();
    expect(posted().token).toBe("fcm-new");
  });

  it("ignores a refreshed token on a device that was never turned on", async () => {
    listener("tokenReceived")({ token: "fcm-new" });
    await flush();
    expect(fetchMock()).not.toHaveBeenCalled();
  });

  it("swallows a failed re-registration", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    fetchMock().mockRejectedValue(new TypeError("offline"));
    listener("tokenReceived")({ token: "fcm-new" });
    await flush();
    expect(fetchMock()).toHaveBeenCalled();
  });

  it("opens a tapped notification's page on this site", () => {
    listener("notificationActionPerformed")({ notification: { data: { url: "/ABC/" } } });
    expect(navigate).toHaveBeenCalledWith(`${ORIGIN}/ABC/`);
  });

  it.each([{ data: { url: "https://evil.example/" } }, { data: undefined }, undefined])(
    "ignores a notification without a page of this site: %p",
    (notification) => {
      listener("notificationActionPerformed")({ notification });
      expect(navigate).not.toHaveBeenCalled();
    }
  );

  /** Click `selector` and return whether the click was taken over. */
  function click(selector: string, init: MouseEventInit = {}): boolean {
    const event = new MouseEvent("click", { bubbles: true, cancelable: true, ...init });
    document.querySelector(selector)!.dispatchEvent(event);
    return event.defaultPrevented;
  }

  it("unregisters before following the logout link", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    expect(click("#out")).toBe(true);
    await flush();
    expect(fetchMock().mock.calls[0][0]).toBe(URLS.unregister);
    expect(navigate).toHaveBeenCalledWith(`${ORIGIN}${LOGOUT_PATH}`);
  });

  it("leaves the logout link alone when the device was never on", () => {
    expect(click("#out")).toBe(false);
  });

  it.each([
    ["#faq", {}],
    ["#plain", {}],
    ["#out", { button: 1 }],
  ])("leaves %s %p alone", (selector, init) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    expect(click(selector, init)).toBe(false);
  });

  it("leaves a click another handler took", () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    document.addEventListener("click", (event) => event.preventDefault(), { capture: true, once: true });
    click("#out");
    expect(navigate).not.toHaveBeenCalled();
  });

  /** Submit `selector` and return whether the submit was taken over. */
  function submit(selector: string): boolean {
    const form = document.querySelector(selector) as HTMLFormElement;
    form.submit = jest.fn();
    const event = new Event("submit", { bubbles: true, cancelable: true });
    form.dispatchEvent(event);
    return event.defaultPrevented;
  }

  it("unregisters before submitting the logout form", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    expect(submit("#logout")).toBe(true);
    await flush();
    expect(fetchMock().mock.calls[0][0]).toBe(URLS.unregister);
    expect((document.querySelector("#logout") as HTMLFormElement).submit).toHaveBeenCalled();
  });

  it("leaves other forms, and a device never on, alone", () => {
    expect(submit("#logout")).toBe(false);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    expect(submit("#other")).toBe(false);
  });

  it("leaves a submit another handler took, and events not from a form", () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(URLS));
    document.addEventListener("submit", (event) => event.preventDefault(), { capture: true, once: true });
    submit("#logout");
    document.body.dispatchEvent(new Event("submit", { bubbles: true }));
    expect(fetchMock()).not.toHaveBeenCalled();
  });
});

describe("installPush with its defaults", () => {
  it("listens on the document and navigates with location.assign", () => {
    installPush();
    const call = plugin.addListener.mock.calls.find((c) => c[0] === "notificationActionPerformed");
    call[1]({ notification: { data: { url: "/faq/" } } });
    expect(window.location.assign).toHaveBeenCalledWith(`${ORIGIN}/faq/`);
  });
});
