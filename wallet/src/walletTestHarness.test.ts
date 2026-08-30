/**
 * @jest-environment jsdom
 */

/**
 * The Selenium mock-wallet harness.
 *
 * It ships in the bundle — behind `window.__WALLET_TEST__`, which the template
 * only emits under `settings.WALLET_TEST_MODE` — so it is production code that
 * happens to exist for tests, and the reason to cover it is that the browser
 * suite depending on it fails in ways that point at the *page* rather than at
 * here. A harness that silently stops signing looks exactly like a broken
 * login flow.
 *
 * `algosdk` and `WalletComponent` are faked: what is under test is the fake
 * `BaseWallet` this file builds, whose state machine the real component drives.
 */

const decodeUnsignedTransaction = jest.fn(() => ({
  signTxn: jest.fn(() => Uint8Array.from([7, 7, 7])),
}));
const mnemonicToSecretKey = jest.fn(() => ({
  addr: { toString: () => "MOCKADDRESS" },
  sk: Uint8Array.from([1, 2, 3]),
}));
jest.mock("algosdk", () => ({
  __esModule: true,
  default: {
    decodeUnsignedTransaction: (...a: unknown[]) =>
      decodeUnsignedTransaction(...a),
    mnemonicToSecretKey: (...a: unknown[]) => mnemonicToSecretKey(...a),
  },
}));

const bind = jest.fn();
const walletComponentCtor = jest.fn();
jest.mock("./walletComponent", () => ({
  WalletComponent: function (this: any, ...args: unknown[]) {
    walletComponentCtor(...args);
    return { bind };
  },
}));

import { install } from "./walletTestHarness";

/** Install and invoke the global, returning what the component was given. */
function installMock(apiBase?: string) {
  install();
  const address = (window as any).__installMockWallet(
    "twenty five words",
    ...(apiBase === undefined ? [] : [apiBase])
  );
  const [wallet, manager, base] = walletComponentCtor.mock.calls[0];
  return { address, wallet, manager, base };
}

beforeEach(() => {
  jest.clearAllMocks();
  document.body.innerHTML = "";
  delete (window as any).__installMockWallet;
});

describe("install", () => {
  it("exposes the global the browser test calls", () => {
    install();
    expect(typeof (window as any).__installMockWallet).toBe("function");
  });

  it("derives the account from the mnemonic and returns its address", () => {
    const { address } = installMock();
    expect(mnemonicToSecretKey).toHaveBeenCalledWith("twenty five words");
    expect(address).toBe("MOCKADDRESS");
  });

  it("defaults the API base", () => {
    expect(installMock().base).toBe("/api/v2/wallet");
  });

  it("honours an explicit API base", () => {
    expect(installMock("/custom/base").base).toBe("/custom/base");
  });
});

describe("the mock card", () => {
  it("is created inside #wallet-connect when the page offers one", () => {
    document.body.innerHTML = '<div id="wallet-connect"></div>';
    installMock();

    const card = document.getElementById("wallet-mock")!;
    expect(card.parentElement!.id).toBe("wallet-connect");
    expect(card.querySelector("#connect-button-mock")).not.toBeNull();
    expect(card.querySelector("#auth-button-mock")).not.toBeNull();
    expect(bind).toHaveBeenCalledWith(card);
  });

  it("falls back to the body when there is no wallet container", () => {
    installMock();
    expect(document.getElementById("wallet-mock")!.parentElement).toBe(
      document.body
    );
  });

  it("reuses a card the page already rendered", () => {
    document.body.innerHTML = '<div id="wallet-mock">existing</div>';
    installMock();
    expect(document.querySelectorAll("#wallet-mock")).toHaveLength(1);
    expect(document.getElementById("wallet-mock")!.textContent).toBe("existing");
  });
});

describe("the fake wallet's state machine", () => {
  it("starts disconnected with no accounts", () => {
    const { wallet } = installMock();
    expect(wallet).toMatchObject({
      id: "mock",
      isConnected: false,
      isActive: false,
      accounts: [],
      activeAccount: null,
    });
  });

  it("connect publishes one account and notifies subscribers", async () => {
    const { wallet } = installMock();
    const listener = jest.fn();
    wallet.subscribe(listener);

    const accounts = await wallet.connect();

    expect(accounts).toEqual([{ name: "Mock Account", address: "MOCKADDRESS" }]);
    expect(wallet.isConnected).toBe(true);
    expect(wallet.activeAccount.address).toBe("MOCKADDRESS");
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it("disconnect clears everything and notifies", async () => {
    const { wallet } = installMock();
    const listener = jest.fn();
    wallet.subscribe(listener);
    await wallet.connect();
    await wallet.disconnect();

    expect(wallet).toMatchObject({
      isConnected: false,
      isActive: false,
      accounts: [],
      activeAccount: null,
    });
    expect(listener).toHaveBeenCalledTimes(2);
  });

  it("setActive flags the wallet active", async () => {
    const { wallet } = installMock();
    await wallet.setActive();
    expect(wallet.isActive).toBe(true);
  });

  it("setActiveAccount switches the address", async () => {
    const { wallet } = installMock();
    await wallet.setActiveAccount("OTHERADDRESS");
    expect(wallet.activeAccount).toEqual({
      name: "Mock Account",
      address: "OTHERADDRESS",
    });
  });

  it("unsubscribing stops the callbacks", async () => {
    const { wallet } = installMock();
    const listener = jest.fn();
    const unsubscribe = wallet.subscribe(listener);
    unsubscribe();
    await wallet.connect();
    expect(listener).not.toHaveBeenCalled();
  });

  it("signs the transaction the component actually built", async () => {
    // The whole point of the harness rather than a stub: a real Ed25519
    // signature over the component's own bytes, so the backend's signature
    // and genesis checks run unchanged.
    const { wallet } = installMock();
    const bytes = Uint8Array.from([4, 5, 6]);

    const signed = await wallet.signTransactions([bytes]);

    expect(decodeUnsignedTransaction).toHaveBeenCalledWith(bytes);
    expect(signed).toEqual([Uint8Array.from([7, 7, 7])]);
  });
});

describe("the fake manager", () => {
  it("pins MainNet, because the backend rejects a TestNet genesis", async () => {
    const { manager } = installMock();
    const params = await manager.algodClient.getTransactionParams().do();

    expect(params.genesisID).toBe("mainnet-v1.0");
    expect(params).toMatchObject({ fee: 0, minFee: 1000, flatFee: true });
  });

  it("decodes the genesis hash to the bytes algosdk wants", async () => {
    const { manager } = installMock();
    const { genesisHash } = await manager.algodClient
      .getTransactionParams()
      .do();

    expect(genesisHash).toBeInstanceOf(Uint8Array);
    expect(genesisHash).toHaveLength(32);
    expect(Buffer.from(genesisHash).toString("base64")).toBe(
      "wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8="
    );
  });
});
