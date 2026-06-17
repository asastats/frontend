/**
 * @jest-environment jsdom
 */

import {
  EvmWalletComponent,
  type EvmConnector,
  type EvmDeps,
} from "./evmWalletComponent";

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

beforeEach(() => {
  (window as any).M = { toast: jest.fn() };
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

    const buttons = root.querySelectorAll(".evm-connect-button");
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
    expect(root.querySelectorAll(".evm-connect-button")).toHaveLength(1);
  });

  it("reveals the error banner when no connectors are found", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps({ listConnectors: () => [] }));
    await c.bind();
    const banner = root.querySelector<HTMLElement>("#evm-app-error")!;
    expect(banner.style.display).toBe("block");
    expect(root.querySelectorAll(".evm-connect-button")).toHaveLength(0);
  });

  it("falls back to the container when no list element is present", async () => {
    document.body.innerHTML = `<div id="evm-wallet-connect"></div>`;
    const root = document.getElementById("evm-wallet-connect")!;
    const c = new EvmWalletComponent(root, undefined, deps());
    await c.bind();
    expect(root.querySelectorAll(".evm-connect-button")).toHaveLength(1);
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
      .querySelector<HTMLElement>(".evm-connect-button")!
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
    expect(nonceBody).toEqual({ address: VALID_ADDR.toLowerCase(), chain: "evm" });
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
    });

    expect(navigate).toHaveBeenCalledWith("/home/");
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
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ text: "user rejected" })
    );
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
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ text: expect.stringContaining("Invalid EVM address") })
    );
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("surfaces a nonce endpoint error", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    mockFetchSequence({ error: "Invalid or missing address" });
    await c.authorizeWith(makeConnector());
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ text: "Invalid or missing address" })
    );
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
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ text: "signature declined" })
    );
  });

  it("surfaces a verify failure message", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    mockFetchSequence(
      { nonce: "N", prefix: "p:" },
      { success: false, error: "No account is linked to this wallet" }
    );
    await c.authorizeWith(makeConnector());
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ text: "No account is linked to this wallet" })
    );
  });

  it("defaults the verify failure message when none is given", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    mockFetchSequence({ nonce: "N", prefix: "p:" }, { success: false });
    await c.authorizeWith(makeConnector());
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ text: "Verification failed" })
    );
  });

  it("passes wallet-derived text to the toast as plain text", async () => {
    const root = setupDOM();
    const c = new EvmWalletComponent(root, undefined, deps());
    const connector = makeConnector({
      connect: jest.fn(async () => {
        throw new Error("<img src=x>");
      }),
    });
    await c.authorizeWith(connector);
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ text: "<img src=x>" })
    );
  });

  it("falls back to a card panel when Materialize is absent", async () => {
    jest.useFakeTimers();
    const root = setupDOM();
    delete (window as any).M;
    const c = new EvmWalletComponent(root, undefined, deps());
    const connector = makeConnector({
      connect: jest.fn(async () => {
        throw new Error("boom");
      }),
    });
    await c.authorizeWith(connector);
    const panel = root.querySelector(".card-panel");
    expect(panel).not.toBeNull();
    expect(panel!.textContent).toBe("boom");
    jest.advanceTimersByTime(5000);
    expect(root.querySelector(".card-panel")).toBeNull();
    jest.useRealTimers();
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
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ text: "plain string failure" })
    );
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
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ text: "Invalid EVM address: undefined" })
    );
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
