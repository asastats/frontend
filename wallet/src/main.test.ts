/**
 * @jest-environment jsdom
 */

import { App } from "./main";

// ─────────────────────────────────────────────────────────────
// Mocks
// ─────────────────────────────────────────────────────────────
const resumeSessionsMock = jest.fn().mockResolvedValue(undefined);
const getWalletMock = jest.fn();

jest.mock("@txnlab/use-wallet", () => {
  const actual = jest.requireActual("@txnlab/use-wallet");
  return {
    ...actual,
    WalletManager: jest.fn().mockImplementation(() => ({
      getWallet: getWalletMock,
      resumeSessions: resumeSessionsMock,
    })),
  };
});

const bindMock = jest.fn();
const destroyMock = jest.fn();
jest.mock("./walletComponent", () => ({
  WalletComponent: jest.fn().mockImplementation(() => ({
    bind: bindMock,
    destroy: destroyMock,
  })),
}));

const resumeStepMock = jest.fn().mockResolvedValue({ kind: "none" });
const offerSignInMock = jest.fn();
jest.mock("./walletResume", () => ({
  ...jest.requireActual("./walletResume"),
  resumeStep: (...args: unknown[]) => resumeStepMock(...args),
  offerSignIn: (...args: unknown[]) => offerSignInMock(...args),
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
    expect(WalletManager).toHaveBeenCalledWith(
      expect.objectContaining({
        defaultNetwork: "mainnet",
      })
    );
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

  /** A `pagehide` event; jsdom has no PageTransitionEvent constructor. */
  function pagehide(persisted: boolean): Event {
    const event = new Event("pagehide");
    Object.defineProperty(event, "persisted", { value: persisted });
    return event;
  }

  it("destroys bound components when the page is unloaded", async () => {
    document.body.innerHTML = '<div id="wallet-connect"></div><div id="wallet-pera"></div>';
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      walletsResponse([{ id: "pera", name: "Pera" }])
    );
    const app = new App();
    await app.init();
    destroyMock.mockClear();
    window.dispatchEvent(pagehide(false));
    expect(destroyMock).toHaveBeenCalled();
  });

  it("keeps them on beforeunload and into the back/forward cache", async () => {
    document.body.innerHTML = '<div id="wallet-connect"></div><div id="wallet-pera"></div>';
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      walletsResponse([{ id: "pera", name: "Pera" }])
    );
    const app = new App();
    await app.init();
    destroyMock.mockClear();
    // A wallet hand-off to wc: fires beforeunload and the page stays (S3)
    window.dispatchEvent(new Event("beforeunload"));
    window.dispatchEvent(pagehide(true));
    expect(destroyMock).not.toHaveBeenCalled();
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

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: A step the phone interrupted (walletResume.ts)
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */
describe("App resume in the app", () => {
  const seen: { managers?: number; text?: string | null } = {};
  const SIGN = { kind: "sign", wallet: "defly", apiBase: "/api/v2/wallet/login" };

  async function start(resumed: unknown, card = '<div id="wallet-pera"><div data-notice="info">lost</div></div>') {
    document.documentElement.classList.add("in-app");
    document.body.innerHTML = `<div id="wallet-connect"></div>${card}<div id="wallet-defly"></div>`;
    (global.fetch as jest.Mock).mockResolvedValueOnce(walletsResponse([{ id: "pera" }, { id: "defly" }]));
    resumeStepMock.mockImplementationOnce(async () => {
      seen.managers = (WalletManager as jest.Mock).mock.calls.length;
      seen.text = document.querySelector("#wallet-pera [data-notice]")?.textContent;
      return resumed;
    });
    const app = new App();
    await app.init();
    document.documentElement.classList.remove("in-app");
  }

  afterEach(() => {
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  });

  it("finishes the step before the manager loads, and says a connect is done", async () => {
    await start({ kind: "connected", wallet: "pera" });
    expect(resumeStepMock).toHaveBeenCalledWith(window.location.href);
    expect(seen).toEqual({ managers: 0, text: "Checking Pera's answer…" });
    expect(document.querySelector("#wallet-pera [data-notice]")!.textContent).toBe(
      "Pera is connected. Tap Sign in to finish."
    );
  });

  it("says when the wallet did not answer", async () => {
    await start({ kind: "lost", wallet: "pera" });
    expect(document.querySelector("#wallet-pera [data-notice]")!.textContent).toBe(
      "Pera did not answer in time, so that step did not finish. Please connect again."
    );
  });

  it("offers to finish a signed sign-in with the cookie's CSRF token", async () => {
    document.cookie = "csrftoken=fromcookie";
    await start({ kind: "signed", step: SIGN, signed: "c2ln" });
    expect(offerSignInMock).toHaveBeenCalledWith(document, SIGN, "c2ln", "fromcookie");
  });

  it("falls back to the page's CSRF input, then to nothing", async () => {
    await start({ kind: "signed", step: SIGN, signed: "c2ln" }, '<input name="csrfmiddlewaretoken" value="frominput"><div id="wallet-pera"></div>');
    expect(offerSignInMock).toHaveBeenLastCalledWith(document, SIGN, "c2ln", "frominput");
    await start({ kind: "signed", step: SIGN, signed: "c2ln" }, '<div id="wallet-pera"></div>');
    expect(offerSignInMock).toHaveBeenLastCalledWith(document, SIGN, "c2ln", "");
  });

  it("does not announce a check for a card it cannot resume", async () => {
    await start({ kind: "none" }, '<div id="wallet-lute"><div data-notice="info">lost</div></div><div id="wallet-pera"></div>');
    expect(document.querySelector("#wallet-lute [data-notice]")!.textContent).toBe("lost");
  });

  it("does nothing outside the app", async () => {
    document.body.innerHTML = '<div id="wallet-connect"></div><div id="wallet-pera"></div>';
    (global.fetch as jest.Mock).mockResolvedValueOnce(walletsResponse([{ id: "pera" }]));
    await new App().init();
    expect(resumeStepMock).not.toHaveBeenCalled();
  });
});
