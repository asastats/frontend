/**
 * @jest-environment jsdom
 */

import { App } from "./main";

// ─────────────────────────────────────────────────────────────
// Mocks
// ─────────────────────────────────────────────────────────────
const resumeSessionsMock = jest.fn().mockResolvedValue(undefined);
const getWalletMock = jest.fn();

jest.mock("@txnlab/use-wallet", () => ({
  WalletId: { PERA: "pera", DEFLY: "defly" },
  WalletManager: jest.fn().mockImplementation(() => ({
    getWallet: getWalletMock,
    resumeSessions: resumeSessionsMock,
  })),
}));

const bindMock = jest.fn();
const destroyMock = jest.fn();
jest.mock("./walletComponent", () => ({
  WalletComponent: jest.fn().mockImplementation(() => ({
    bind: bindMock,
    destroy: destroyMock,
  })),
}));

import { WalletManager } from "@txnlab/use-wallet";
import { WalletComponent } from "./walletComponent";

function walletsResponse(data: any) {
  return { ok: true, json: async () => data };
}

beforeEach(() => {
  jest.clearAllMocks();
  document.body.innerHTML = "";
  (global.fetch as jest.Mock).mockReset();
  getWalletMock.mockImplementation((id: string) => ({ id }));
});

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Initialization gating
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("App initialization gating", () => {
  it("no-ops when no wallet elements are present", async () => {
    const app = new App();
    await app.init();
    expect(global.fetch).not.toHaveBeenCalled();
    expect(app.walletManager).toBeNull();
  });

  it("initializes when a wallet card is present", async () => {
    document.body.innerHTML = '<div id="wallet-pera"></div>';
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      walletsResponse([{ id: "pera", name: "Pera" }])
    );
    const app = new App();
    await app.init();
    expect(global.fetch).toHaveBeenCalledWith("/api/v2/wallet/wallets/");
    expect(app.walletManager).not.toBeNull();
  });
});

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Wallet wiring
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("App wallet wiring", () => {
  it("builds a mainnet WalletManager with the fetched wallet ids", async () => {
    document.body.innerHTML = '<div id="wallet-connect"></div><div id="wallet-pera"></div>';
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      walletsResponse([{ id: "pera", name: "Pera" }])
    );
    const app = new App();
    await app.init();
    expect(WalletManager).toHaveBeenCalledWith({
      wallets: ["pera"],
      defaultNetwork: "mainnet",
    });
  });

  it("binds a WalletComponent for each rendered wallet card", async () => {
    document.body.innerHTML =
      '<div id="wallet-connect"></div><div id="wallet-pera"></div><div id="wallet-defly"></div>';
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      walletsResponse([
        { id: "pera", name: "Pera" },
        { id: "defly", name: "Defly" },
      ])
    );
    const app = new App();
    await app.init();
    expect(WalletComponent).toHaveBeenCalledTimes(2);
    expect(bindMock).toHaveBeenCalledTimes(2);
    expect(resumeSessionsMock).toHaveBeenCalledTimes(1);
  });

  it("destroys bound components on beforeunload", async () => {
    document.body.innerHTML = '<div id="wallet-connect"></div><div id="wallet-pera"></div>';
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      walletsResponse([{ id: "pera", name: "Pera" }])
    );
    const app = new App();
    await app.init();
    destroyMock.mockClear();
    window.dispatchEvent(new Event("beforeunload"));
    expect(destroyMock).toHaveBeenCalled();
  });

  it("skips wallets whose card is not rendered", async () => {
    document.body.innerHTML = '<div id="wallet-connect"></div><div id="wallet-pera"></div>';
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      walletsResponse([
        { id: "pera", name: "Pera" },
        { id: "defly", name: "Defly" },
      ])
    );
    const app = new App();
    await app.init();
    expect(WalletComponent).toHaveBeenCalledTimes(1);
  });

  it("passes a data-api-base override to components and the fetch", async () => {
    document.body.innerHTML =
      '<div id="wallet-connect" data-api-base="/custom/wallet"></div><div id="wallet-pera"></div>';
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      walletsResponse([{ id: "pera", name: "Pera" }])
    );
    const app = new App();
    await app.init();
    expect(global.fetch).toHaveBeenCalledWith("/custom/wallet/wallets/");
    expect(WalletComponent).toHaveBeenCalledWith(
      expect.anything(),
      expect.anything(),
      "/custom/wallet"
    );
  });
});

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Failure handling
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("App failure handling", () => {
  it("reveals #app-error when the wallets fetch fails", async () => {
    document.body.innerHTML =
      '<div id="wallet-pera"></div><div id="app-error" style="display:none"></div>';
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false });
    const app = new App();
    await app.init();
    const errorDiv = document.getElementById("app-error")!;
    expect(errorDiv.style.display).toBe("block");
  });
});

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Test harness gate
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("App test harness gate", () => {
  it("installs the mock wallet harness when the flag is set", () => {
    const install = jest.fn();
    jest.doMock("./walletTestHarness", () => ({ install }));
    (window as any).__WALLET_TEST__ = true;

    jest.isolateModules(() => {
      require("./main");
    });

    expect(install).toHaveBeenCalled();
    delete (window as any).__WALLET_TEST__;
    jest.dontMock("./walletTestHarness");
  });
});
