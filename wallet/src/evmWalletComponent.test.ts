/**
 * @jest-environment jsdom
 */

import { NOTIFY_EVENT } from "./notify";
import {
  EvmWalletComponent,
  type EvmConnector,
  type EvmDeps,
} from "./evmWalletComponent";
import { EVM_RESUME_KEY } from "./walletResumeEvm";

/**
 * Capture messages the package surfaces.
 *
 * The package no longer calls a framework global; it dispatches a cancelable
 * `asastats:notify` event and lets the host render it. Claiming the event here
 * (preventDefault) is what a real host does, and it suppresses the built-in
 * fallback notice so these assertions see one channel, not two.
 */
function captureNotices(): { texts: string[]; stop: () => void } {
  const texts: string[] = [];
  const onNotify = (event: Event) => {
    texts.push((event as CustomEvent<{ message: string }>).detail.message);
    event.preventDefault();
  };
  document.addEventListener(NOTIFY_EVENT, onNotify);
  return { texts, stop: () => document.removeEventListener(NOTIFY_EVENT, onNotify) };
}

const VALID_ADDR = "0x52908400098527886E0F7030069857D2E4169EE7";

function setupDOM(apiBase = "/api/v2/wallet/login"): HTMLElement {
  document.body.innerHTML = `
    <div id="evm-wallet-connect" data-api-base="${apiBase}" data-wc-project-id="">
      <input type="hidden" name="csrfmiddlewaretoken" value="tok123">
      <div id="evm-app-error" style="display:none"></div>
      <div id="evm-wallet-list"></div>
    </div>`;
  return document.getElementById("evm-wallet-connect")!;
}

function makeConnector(over: Partial<EvmConnector> = {}): EvmConnector {
  return {
    id: "io.metamask",
    name: "MetaMask",
    connect: jest.fn(async () => ({
      provider: { request: jest.fn() },
      address: VALID_ADDR,
    })),
    ...over,
  };
}

function mockFetchSequence(...responses: unknown[]) {
  const fn = global.fetch as jest.Mock;
  fn.mockReset();
  responses.forEach((r) =>
    fn.mockResolvedValueOnce({ json: async () => r } as Response)
  );
}

function deps(over: Partial<EvmDeps> = {}): EvmDeps {
  return {
    listConnectors: () => [makeConnector()],
    sign: jest.fn(async () => "0xsignature"),
    navigate: jest.fn(),
    ...over,
  };
}

let notices: { texts: string[]; stop: () => void };

beforeEach(() => {
  notices = captureNotices();
});

afterEach(() => {
  notices.stop();
});

// ─────────────────────────────────────────────────────────────
// render
// ─────────────────────────────────────────────────────────────
describe("EvmWalletComponent.render", () => {
  it("renders one button per connector with name and icon", async () => {
    const root = setupDOM();
    const connectors = [
      makeConnector({ id: "io.metamask", name: "MetaMask", icon: "data:," }),
      makeConnector({ id: "com.coinbase", name: "Coinbase" }),
    ];
    const c = new EvmWalletComponent(root, undefined, deps({ listConnectors: () => connectors }));
    await c.bind();

    const buttons = root.querySelectorAll("[data-wallet-connect]");
    expect(buttons).toHaveLength(2);
    expect(buttons[0].textContent).toContain("MetaMask");
    expect(buttons[0].querySelector("img")).not.toBeNull();
    expect(buttons[1].querySelector("img")).toBeNull();
    expect((buttons[0] as HTMLElement).dataset.connectorId).toBe("io.metamask");
  });

  it("awaits an async connector list", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(
      root,
      undefined,
      deps({ listConnectors: async () => [makeConnector()] })
    );
    await c.bind();
    expect(root.querySelectorAll("[data-wallet-connect]")).toHaveLength(1);
  });

  it("reveals the error banner when no connectors are found", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps({ listConnectors: () => [] }));
    await c.bind();
    const banner = root.querySelector<HTMLElement>("#evm-app-error")!;
    expect(banner.style.display).toBe("block");
    expect(root.querySelectorAll("[data-wallet-connect]")).toHaveLength(0);
  });

  it("falls back to the container when no list element is present", async () => {
    document.body.innerHTML = `<div id="evm-wallet-connect"></div>`;
    const root = document.getElementById("evm-wallet-connect")!;
    const c = new EvmWalletComponent(root, undefined, deps());
    await c.bind();
    expect(root.querySelectorAll("[data-wallet-connect]")).toHaveLength(1);
  });
});

// ─────────────────────────────────────────────────────────────
// click delegation
// ─────────────────────────────────────────────────────────────
describe("EvmWalletComponent click delegation", () => {
  it("routes a connector-button click to authorizeWith", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    const spy = jest
      .spyOn(c as any, "authorizeWith")
      .mockResolvedValue(undefined);
    await c.bind();

    root
      .querySelector<HTMLElement>("[data-wallet-connect]")!
      .dispatchEvent(new MouseEvent("click", { bubbles: true }));
    await Promise.resolve();
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("ignores clicks outside a connector button", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    const spy = jest
      .spyOn(c as any, "authorizeWith")
      .mockResolvedValue(undefined);
    await c.bind();

    root
      .querySelector<HTMLElement>("#evm-wallet-list")!
      .dispatchEvent(new MouseEvent("click", { bubbles: true }));
    await Promise.resolve();
    expect(spy).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────
// authorizeWith — happy paths
// ─────────────────────────────────────────────────────────────
describe("EvmWalletComponent.authorizeWith success", () => {
  it("runs nonce → sign → verify and navigates, with CSRF and evm chain", async () => {
    const root = setupDOM();
    const sign = jest.fn(async () => "0xdeadbeef");
    const navigate = jest.fn();
    const connector = makeConnector();
    const c = new EvmWalletComponent(
      root,
      "/api/v2/wallet/login",
      deps({ sign, navigate })
    );
    mockFetchSequence(
      { nonce: "N1", prefix: "asastats-auth:" },
      { success: true, redirect_url: "/home/" }
    );

    await c.authorizeWith(connector);

    const fetchMock = global.fetch as jest.Mock;
    expect(fetchMock.mock.calls[0][0]).toBe("/api/v2/wallet/login/nonce/");
    const nonceBody = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(nonceBody).toEqual({
      address: VALID_ADDR.toLowerCase(),
      chain: "evm",
      binding: expect.stringMatching(/^[0-9a-f]{64}$/),
    });
    expect(fetchMock.mock.calls[0][1].headers["X-CSRFToken"]).toBe("tok123");

    expect(sign).toHaveBeenCalledWith(
      expect.anything(),
      VALID_ADDR.toLowerCase(),
      "asastats-auth:N1"
    );

    expect(fetchMock.mock.calls[1][0]).toBe("/api/v2/wallet/login/verify/");
    const verifyBody = JSON.parse(fetchMock.mock.calls[1][1].body);
    expect(verifyBody).toEqual({
      nonce: "N1",
      chain: "evm",
      signature: "0xdeadbeef",
      binding: nonceBody.binding,
    });

    expect(navigate).toHaveBeenCalledWith("/home/");
  });

  it("binds each sign-in attempt to a new secret (audit E2)", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, "/api/v2/wallet/login", deps());
    mockFetchSequence(
      { nonce: "N1", prefix: "p:" },
      { success: true, redirect_url: "/" },
      { nonce: "N2", prefix: "p:" },
      { success: true, redirect_url: "/" }
    );
    await c.authorizeWith(makeConnector());
    await c.authorizeWith(makeConnector());
    const bodies = (global.fetch as jest.Mock).mock.calls.map((call) => JSON.parse(call[1].body));
    expect(bodies[1].binding).toBe(bodies[0].binding);
    expect(bodies[3].binding).toBe(bodies[2].binding);
    expect(bodies[2].binding).not.toBe(bodies[0].binding);
  });

  it("uses the link API base when constructed for linking", async () => {
    const root = setupDOM("/api/v2/wallet/link");
    const c = new EvmWalletComponent(root, "/api/v2/wallet/link", deps());
    mockFetchSequence(
      { nonce: "N", prefix: "p:" },
      { success: true, redirect_url: "/profile/" }
    );
    await c.authorizeWith(makeConnector());
    const fetchMock = global.fetch as jest.Mock;
    expect(fetchMock.mock.calls[0][0]).toBe("/api/v2/wallet/link/nonce/");
    expect(fetchMock.mock.calls[1][0]).toBe("/api/v2/wallet/link/verify/");
  });

  it("falls back to root when no redirect_url is returned", async () => {
    const root = setupDOM();
    const navigate = jest.fn();
    const c = new EvmWalletComponent(root, undefined, deps({ navigate }));
    mockFetchSequence({ nonce: "N", prefix: "p:" }, { success: true });
    await c.authorizeWith(makeConnector());
    expect(navigate).toHaveBeenCalledWith("/");
  });

  it("navigates via window.location by default", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(
      root,
      undefined,
      deps({ navigate: undefined })
    );
    mockFetchSequence(
      { nonce: "N", prefix: "p:" },
      { success: true, redirect_url: "/dest/" }
    );
    await c.authorizeWith(makeConnector());
    expect(window.location.href).toBe("/dest/");
  });

  it("reads the CSRF token from the cookie when present", async () => {
    const root = setupDOM();
    document.cookie = "csrftoken=cookietok";
    const c = new EvmWalletComponent(root, undefined, deps());
    mockFetchSequence({ nonce: "N", prefix: "p:" }, { success: true });
    await c.authorizeWith(makeConnector());
    const fetchMock = global.fetch as jest.Mock;
    expect(fetchMock.mock.calls[0][1].headers["X-CSRFToken"]).toBe("cookietok");
    // reset cookie for other tests
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  });
});

// ─────────────────────────────────────────────────────────────
// authorizeWith — failures (all surface a toast, none navigate)
// ─────────────────────────────────────────────────────────────
describe("EvmWalletComponent.authorizeWith failures", () => {
  it("toasts when the connector fails to open", async () => {
    const root = setupDOM();
    const navigate = jest.fn();
    const c = new EvmWalletComponent(root, undefined, deps({ navigate }));
    const connector = makeConnector({
      connect: jest.fn(async () => {
        throw new Error("user rejected");
      }),
    });
    await c.authorizeWith(connector);
    expect(notices.texts).toContain("user rejected");
    expect(navigate).not.toHaveBeenCalled();
  });

  it("rejects an invalid recovered address", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    const connector = makeConnector({
      connect: jest.fn(async () => ({
        provider: { request: jest.fn() },
        address: "0xnothex",
      })),
    });
    await c.authorizeWith(connector);
    expect(notices.texts).toContainEqual(expect.stringContaining("Invalid EVM address"));
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("surfaces a nonce endpoint error", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    mockFetchSequence({ error: "Invalid or missing address" });
    await c.authorizeWith(makeConnector());
    expect(notices.texts).toContain("Invalid or missing address");
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("surfaces a signer failure", async () => {
    const root = setupDOM();
    const sign = jest.fn(async () => {
      throw new Error("signature declined");
    });
    const c = new EvmWalletComponent(root, undefined, deps({ sign }));
    mockFetchSequence({ nonce: "N", prefix: "p:" });
    await c.authorizeWith(makeConnector());
    expect(notices.texts).toContain("signature declined");
  });

  it("surfaces a verify failure message", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    mockFetchSequence(
      { nonce: "N", prefix: "p:" },
      { success: false, error: "No account is linked to this wallet" }
    );
    await c.authorizeWith(makeConnector());
    expect(notices.texts).toContain("No account is linked to this wallet");
  });

  it("defaults the verify failure message when none is given", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    mockFetchSequence({ nonce: "N", prefix: "p:" }, { success: false });
    await c.authorizeWith(makeConnector());
    expect(notices.texts).toContain("Verification failed");
  });

  it("passes wallet-derived text through as plain text", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    const connector = makeConnector({
      connect: jest.fn(async () => {
        throw new Error("<img src=x>");
      }),
    });
    await c.authorizeWith(connector);
    expect(notices.texts).toContain("<img src=x>");
  });

  it("appends a plain notice when no host claims the message", async () => {
    jest.useFakeTimers();
    const root = setupDOM();
    // No listener: the event goes uncancelled and the built-in fallback runs.
    notices.stop();
    const c = new EvmWalletComponent(root, undefined, deps());
    const connector = makeConnector({
      connect: jest.fn(async () => {
        throw new Error("boom");
      }),
    });
    await c.authorizeWith(connector);
    const notice = root.querySelector('[data-notice="error"]');
    expect(notice).not.toBeNull();
    expect(notice!.textContent).toBe("boom");
    expect(notice!.getAttribute("role")).toBe("alert");
    jest.advanceTimersByTime(5000);
    expect(root.querySelector("[data-notice]")).toBeNull();
    jest.useRealTimers();
    notices = captureNotices();
  });

  it("stringifies non-Error throwables", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    const connector = makeConnector({
      connect: jest.fn(async () => {
        // eslint-disable-next-line no-throw-literal
        throw "plain string failure";
      }),
    });
    await c.authorizeWith(connector);
    expect(notices.texts).toContain("plain string failure");
  });

  it("rejects a missing recovered address with an 'undefined' message", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    const connector = makeConnector({
      connect: jest.fn(async () => ({
        provider: { request: jest.fn() },
        address: "",
      })),
    });
    await c.authorizeWith(connector);
    expect(notices.texts).toContain("Invalid EVM address: undefined");
  });

  it("sends an empty CSRF token when neither cookie nor input is present", async () => {
    document.body.innerHTML = `
      <div id="evm-wallet-connect" data-api-base="/api/v2/wallet/login">
        <div id="evm-wallet-list"></div>
      </div>`;
    const root = document.getElementById("evm-wallet-connect")!;
    const c = new EvmWalletComponent(root, undefined, deps());
    mockFetchSequence({ nonce: "N", prefix: "p:" }, { success: true });
    await c.authorizeWith(makeConnector());
    const fetchMock = global.fetch as jest.Mock;
    expect(fetchMock.mock.calls[0][1].headers["X-CSRFToken"]).toBe("");
  });
});

describe("EvmWalletComponent with WalletConnect in the app (walletResumeEvm.ts)", () => {
  const wc = (over: Partial<EvmConnector> = {}) => makeConnector({ id: "walletconnect", name: "WalletConnect", ...over });
  const NONCE = "0123456789abcdef0123456789abcdef";

  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.add("in-app");
  });

  afterEach(() => {
    document.documentElement.classList.remove("in-app");
  });

  it("keeps the connect step, then the sign step, and drops it when done", async () => {
    const root = setupDOM();
    const seen: unknown[] = [];
    const connect = jest.fn(async () => {
      seen.push(JSON.parse(localStorage.getItem(EVM_RESUME_KEY)!));
      return { provider: { request: jest.fn() }, address: VALID_ADDR };
    });
    const sign = jest.fn(async () => {
      seen.push(JSON.parse(localStorage.getItem(EVM_RESUME_KEY)!));
      return "0xsignature";
    });
    const c = new EvmWalletComponent(root, undefined, deps({ sign }));
    mockFetchSequence({ nonce: NONCE, prefix: "asastats-auth:" }, { success: true });

    await expect(c.authorizeWith(wc({ connect }))).resolves.toBe(true);

    expect(seen[0]).toMatchObject({ kind: "connect", url: window.location.href });
    expect(seen[1]).toMatchObject({
      kind: "sign",
      address: VALID_ADDR.toLowerCase(),
      nonce: NONCE,
      prefix: "asastats-auth:",
      apiBase: "/api/v2/wallet/login",
    });
    expect((seen[1] as { binding: string }).binding).toMatch(/^[0-9a-f]{64}$/);
    expect(localStorage.getItem(EVM_RESUME_KEY)).toBeNull();
  });

  it("drops the step when the flow fails", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    const connector = wc({ connect: jest.fn().mockRejectedValue(new Error("closed")) });
    await expect(c.authorizeWith(connector)).resolves.toBe(false);
    expect(localStorage.getItem(EVM_RESUME_KEY)).toBeNull();
  });

  it("keeps nothing for an injected wallet", async () => {
    const root = setupDOM();
    const sign = jest.fn(async () => {
      expect(localStorage.getItem(EVM_RESUME_KEY)).toBeNull();
      return "0xsignature";
    });
    const c = new EvmWalletComponent(root, undefined, deps({ sign }));
    mockFetchSequence({ nonce: NONCE, prefix: "p:" }, { success: true });
    await c.authorizeWith(makeConnector());
    expect(sign).toHaveBeenCalled();
  });

  it("deletes the signature WalletConnect kept once it is used (E4)", async () => {
    const root = setupDOM();
    const history = { values: [{ id: 1, topic: "t", request: { method: "wc_sessionRequest", params: { request: { method: "personal_sign" } } } }], delete: jest.fn() };
    const provider = { request: jest.fn(), session: { topic: "t" }, signer: { client: { core: { history } } } };
    const c = new EvmWalletComponent(root, undefined, deps());
    mockFetchSequence({ nonce: NONCE, prefix: "p:" }, { success: true });
    await c.authorizeWith(wc({ connect: jest.fn(async () => ({ provider, address: VALID_ADDR })) }));
    expect(history.delete).toHaveBeenCalledWith("t", 1);
  });

  it("signs in with a restored provider", async () => {
    const root = setupDOM();
    const sign = jest.fn(async () => "0xsignature");
    const c = new EvmWalletComponent(root, undefined, deps({ sign }));
    const provider = { request: jest.fn() };
    mockFetchSequence({ nonce: NONCE, prefix: "p:" }, { success: true });
    await expect(c.signInWith(provider, VALID_ADDR, "Trust Wallet")).resolves.toBe(true);
    expect(sign).toHaveBeenCalledWith(provider, VALID_ADDR.toLowerCase(), `p:${NONCE}`);
  });

  it("verifies a collected signature and follows the redirect", async () => {
    const root = setupDOM();
    const navigate = jest.fn();
    const c = new EvmWalletComponent(root, undefined, deps({ navigate }));
    mockFetchSequence({ success: true, redirect_url: "/home/" });
    await expect(c.verify("/api/v2/wallet/link", NONCE, "0xsig", "b".repeat(64))).resolves.toBe(true);
    const fetchMock = global.fetch as jest.Mock;
    expect(fetchMock.mock.calls[0][0]).toBe("/api/v2/wallet/link/verify/");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      nonce: NONCE,
      chain: "evm",
      signature: "0xsig",
      binding: "b".repeat(64),
    });
    expect(navigate).toHaveBeenCalledWith("/home/");
  });

  it("says why a collected signature was refused", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    mockFetchSequence({ success: false, error: "Nonce expired" });
    await expect(c.verify("/api/v2/wallet/login", NONCE, "0xsig", "b".repeat(64))).resolves.toBe(false);
    expect(notices.texts).toContain("Nonce expired");
  });

  it("stringifies a non-Error verify failure", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps({ fetchFn: jest.fn().mockRejectedValue("offline") }));
    await expect(c.verify("/api/v2/wallet/login", NONCE, "0xsig", "b".repeat(64))).resolves.toBe(false);
    expect(notices.texts).toContain("offline");
  });
});

describe("EvmWalletComponent in the login dialog", () => {
  function dialogDOM() {
    document.body.innerHTML = `
      <dialog id="modalLogin" open>
        <div id="evm-wallet-connect"><div id="evm-wallet-list"></div></div>
      </dialog>`;
    const dialog = document.getElementById("modalLogin") as HTMLDialogElement;
    dialog.close = jest.fn(() => dialog.removeAttribute("open"));
    dialog.showModal = jest.fn(() => dialog.setAttribute("open", ""));
    return { dialog, root: document.getElementById("evm-wallet-connect")! };
  }

  it("steps aside while WalletConnect's picker is up, then comes back", async () => {
    const { dialog, root } = dialogDOM();
    const connect = jest.fn(async () => {
      expect(dialog.open).toBe(false);
      throw new Error("closed");
    });
    const c = new EvmWalletComponent(root, undefined, deps());
    await c.authorizeWith(makeConnector({ id: "walletconnect", connect }));
    expect(dialog.close).toHaveBeenCalled();
    expect(dialog.showModal).toHaveBeenCalled();
    expect(dialog.open).toBe(true);
  });

  it("does not reopen a dialog the reader already reopened", async () => {
    const { dialog, root } = dialogDOM();
    const connect = jest.fn(async () => {
      dialog.setAttribute("open", "");
      return { provider: { request: jest.fn() }, address: "" };
    });
    const c = new EvmWalletComponent(root, undefined, deps());
    await c.authorizeWith(makeConnector({ id: "walletconnect", connect }));
    expect(dialog.showModal).not.toHaveBeenCalled();
  });

  it("stays for an injected wallet", async () => {
    const { dialog, root } = dialogDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    await c.authorizeWith(makeConnector({ connect: jest.fn().mockRejectedValue(new Error("x")) }));
    expect(dialog.close).not.toHaveBeenCalled();
  });
});
