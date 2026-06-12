/**
 * @jest-environment jsdom
 */

import { WalletComponent } from "./WalletComponent";

// ─────────────────────────────────────────────────────────────
// algosdk mock (only the symbols WalletComponent imports)
// ─────────────────────────────────────────────────────────────
jest.mock("algosdk", () => ({
  makePaymentTxnWithSuggestedParamsFromObject: jest.fn(() => ({ txn: true })),
  encodeUnsignedTransaction: jest.fn(() => new Uint8Array([1, 2, 3])),
  isValidAddress: jest.fn(() => true),
}));

let unsubscribeMock = jest.fn();

const mockWallet: any = {
  id: "pera",
  metadata: { name: "Pera" },
  isConnected: false,
  isActive: false,
  accounts: [],
  activeAccount: null,
  subscribe: jest.fn((cb) => {
    mockWallet._cb = cb;
    return unsubscribeMock;
  }),
  connect: jest.fn(),
  disconnect: jest.fn(),
  setActive: jest.fn(),
  setActiveAccount: jest.fn(),
  signTransactions: jest.fn(async () => [new Uint8Array([10, 11, 12])]),
};

const mockManager: any = {
  algodClient: {
    getTransactionParams: jest.fn().mockReturnValue({
      do: jest.fn().mockResolvedValue({ fee: 1000 }),
    }),
  },
};

function setupDOM(): HTMLElement {
  document.body.innerHTML = `
    <div id="wallet-pera">
      <h4>Pera</h4>
      <button id="connect-button-pera"></button>
      <button id="disconnect-button-pera"></button>
      <button id="set-active-button-pera"></button>
      <button id="auth-button-pera"></button>
      <select class="browser-default"></select>
    </div>
  `;
  return document.getElementById("wallet-pera")!;
}

let component: WalletComponent;
let root: HTMLElement;

beforeEach(() => {
  jest.clearAllMocks();
  unsubscribeMock = jest.fn();
  mockWallet.isConnected = false;
  mockWallet.isActive = false;
  mockWallet.accounts = [];
  mockWallet.activeAccount = null;
  mockWallet.subscribe.mockImplementation((cb: any) => {
    mockWallet._cb = cb;
    return unsubscribeMock;
  });
  (global.fetch as jest.Mock).mockReset();
  document.cookie = "csrftoken=tok123";
  root = setupDOM();
  component = new WalletComponent(mockWallet, mockManager);
  component.bind(root);
});

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Rendering
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("WalletComponent rendering", () => {
  it("shows connect button when disconnected", () => {
    mockWallet._cb(mockWallet);
    const connectBtn = root.querySelector<HTMLButtonElement>("#connect-button-pera")!;
    const disconnectBtn = root.querySelector<HTMLButtonElement>("#disconnect-button-pera")!;
    expect(connectBtn.style.display).toBe("block");
    expect(disconnectBtn.style.display).toBe("none");
  });

  it("adds the Active badge when connected and active", () => {
    mockWallet.isConnected = true;
    mockWallet.isActive = true;
    mockWallet.accounts = [{ address: "AAAAAAAAAAAAA" }];
    mockWallet.activeAccount = mockWallet.accounts[0];
    mockWallet._cb(mockWallet);
    const badge = root.querySelector("h4 .badge");
    expect(badge).not.toBeNull();
    expect(badge?.textContent).toBe("Active");
  });

  it("renders a disabled option when connected with no accounts", () => {
    mockWallet.isConnected = true;
    mockWallet.accounts = [];
    mockWallet._cb(mockWallet);
    const option = root.querySelector<HTMLOptionElement>("select option")!;
    expect(option.textContent).toBe("No accounts");
    expect(option.disabled).toBe(true);
  });

  it("lists accounts and preselects the active one", () => {
    mockWallet.isConnected = true;
    mockWallet.accounts = [{ address: "ABCDEF123456GHIJKL" }];
    mockWallet.activeAccount = mockWallet.accounts[0];
    mockWallet._cb(mockWallet);
    const option = root.querySelector<HTMLOptionElement>("select option")!;
    expect(option.value).toBe("ABCDEF123456GHIJKL");
    expect(option.selected).toBe(true);
  });
});

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Interaction
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("WalletComponent interaction", () => {
  it("connect button calls wallet.connect", () => {
    root.querySelector<HTMLButtonElement>("#connect-button-pera")!.click();
    expect(mockWallet.connect).toHaveBeenCalledTimes(1);
  });

  it("disconnect button calls wallet.disconnect", () => {
    root.querySelector<HTMLButtonElement>("#disconnect-button-pera")!.click();
    expect(mockWallet.disconnect).toHaveBeenCalledTimes(1);
  });

  it("set-active button calls wallet.setActive", () => {
    root.querySelector<HTMLButtonElement>("#set-active-button-pera")!.click();
    expect(mockWallet.setActive).toHaveBeenCalledTimes(1);
  });

  it("account dropdown change calls wallet.setActiveAccount", () => {
    mockWallet.isConnected = true;
    mockWallet.accounts = [{ address: "MOCKADDR" }];
    mockWallet.activeAccount = mockWallet.accounts[0];
    mockWallet._cb(mockWallet);
    const select = root.querySelector<HTMLSelectElement>("select")!;
    select.value = "MOCKADDR";
    select.dispatchEvent(new Event("change", { bubbles: true }));
    expect(mockWallet.setActiveAccount).toHaveBeenCalledWith("MOCKADDR");
  });

  it("auth button click dispatches to auth", () => {
    const spy = jest.spyOn(component, "auth").mockResolvedValue(undefined);
    root.querySelector<HTMLButtonElement>("#auth-button-pera")!.click();
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("removes the Active badge when the wallet becomes inactive", () => {
    mockWallet.isConnected = true;
    mockWallet.isActive = true;
    mockWallet.accounts = [{ address: "AAAAAAAAAAAAA" }];
    mockWallet.activeAccount = mockWallet.accounts[0];
    mockWallet._cb(mockWallet);
    expect(root.querySelector("h4 .badge")).not.toBeNull();
    mockWallet.isActive = false;
    mockWallet._cb(mockWallet);
    expect(root.querySelector("h4 .badge")).toBeNull();
  });
});

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Authorization
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("WalletComponent auth", () => {
  function mockFetchSequence(nonceJson: any, verifyJson: any) {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => nonceJson })
      .mockResolvedValueOnce({ ok: true, json: async () => verifyJson });
  }

  it("posts nonce then verify and redirects on success", async () => {
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    mockFetchSequence(
      { nonce: "n1", prefix: "asastats-auth:" },
      { success: true, redirect_url: "/profile/" }
    );
    await component.auth();
    const calls = (global.fetch as jest.Mock).mock.calls;
    expect(calls[0][0]).toBe("/api/v2/wallet/nonce/");
    expect(calls[1][0]).toBe("/api/v2/wallet/verify/");
    const verifyBody = JSON.parse(calls[1][1].body);
    expect(verifyBody.chain).toBe("algorand");
    expect(verifyBody.nonce).toBe("n1");
    expect(window.location.href).toBe("/profile/");
  });

  it("sends the chain field and CSRF header on the nonce request", async () => {
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    mockFetchSequence(
      { nonce: "n1", prefix: "asastats-auth:" },
      { success: true, redirect_url: "/profile/" }
    );
    await component.auth();
    const nonceCall = (global.fetch as jest.Mock).mock.calls[0];
    expect(JSON.parse(nonceCall[1].body).chain).toBe("algorand");
    expect(nonceCall[1].headers["X-CSRFToken"]).toBe("tok123");
  });

  it("does not redirect when the nonce request errors", async () => {
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ error: "Invalid address" }),
    });
    window.location.href = "";
    await component.auth();
    expect(window.location.href).toBe("");
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("does not redirect when verification fails", async () => {
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    mockFetchSequence(
      { nonce: "n1", prefix: "asastats-auth:" },
      { success: false, error: "Signature verification failed" }
    );
    window.location.href = "";
    await component.auth();
    expect(window.location.href).toBe("");
  });

  it("rejects an invalid active address before any fetch", async () => {
    const algosdk = require("algosdk");
    (algosdk.isValidAddress as jest.Mock).mockReturnValueOnce(false);
    mockWallet.activeAccount = { address: "BAD" };
    await component.auth();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("reads the CSRF token from a hidden input when no cookie is set", async () => {
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.body.innerHTML += '<input name="csrfmiddlewaretoken" value="hiddentok" />';
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    mockFetchSequence(
      { nonce: "n1", prefix: "asastats-auth:" },
      { success: true, redirect_url: "/profile/" }
    );
    await component.auth();
    const nonceCall = (global.fetch as jest.Mock).mock.calls[0];
    expect(nonceCall[1].headers["X-CSRFToken"]).toBe("hiddentok");
  });

  it("surfaces errors via a Materialize toast when available", async () => {
    const toast = jest.fn();
    (window as any).M = { toast };
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ error: "boom" }),
    });
    await component.auth();
    expect(toast).toHaveBeenCalledWith(
      expect.objectContaining({ html: "boom" })
    );
    delete (window as any).M;
  });

  it("errors when the wallet returns no signed transaction", async () => {
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    mockWallet.signTransactions.mockResolvedValueOnce([undefined]);
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ nonce: "n1", prefix: "asastats-auth:" }),
    });
    window.location.href = "";
    await component.auth();
    expect(window.location.href).toBe("");
    // only the nonce request fired; verify was never reached
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("falls back to a generic message when verify returns no error text", async () => {
    const toast = jest.fn();
    (window as any).M = { toast };
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    mockFetchSequence(
      { nonce: "n1", prefix: "asastats-auth:" },
      { success: false }
    );
    await component.auth();
    expect(toast).toHaveBeenCalledWith(
      expect.objectContaining({ html: "Verification failed" })
    );
    delete (window as any).M;
  });

  it("handles a non-Error rejection", async () => {
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    (global.fetch as jest.Mock).mockRejectedValueOnce("network down");
    window.location.href = "";
    await component.auth();
    expect(window.location.href).toBe("");
  });

  it("throws 'undefined' when there is no active account", async () => {
    mockWallet.activeAccount = null;
    await component.auth();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("sends an empty CSRF token when none can be found", async () => {
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    mockFetchSequence(
      { nonce: "n1", prefix: "asastats-auth:" },
      { success: true, redirect_url: "/profile/" }
    );
    await component.auth();
    const nonceCall = (global.fetch as jest.Mock).mock.calls[0];
    expect(nonceCall[1].headers["X-CSRFToken"]).toBe("");
  });
});

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Lifecycle
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("WalletComponent lifecycle", () => {
  it("destroy unsubscribes from wallet state", () => {
    component.destroy();
    expect(unsubscribeMock).toHaveBeenCalledTimes(1);
  });

  it("accepts a custom apiBase for forks", async () => {
    component = new WalletComponent(mockWallet, mockManager, "/custom/wallet");
    component.bind(root);
    mockWallet.activeAccount = { address: "ACTIVEADDR" };
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ nonce: "n1", prefix: "p:" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ success: true, redirect_url: "/profile/" }) });
    await component.auth();
    expect((global.fetch as jest.Mock).mock.calls[0][0]).toBe("/custom/wallet/nonce/");
  });
});
