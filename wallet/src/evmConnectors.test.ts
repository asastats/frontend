/**
 * @jest-environment jsdom
 */

/**
 * The browser adapters behind the EVM wallet picker.
 *
 * This file was excluded from coverage on the grounds that it "touches wallet
 * globals, the EIP-6963 event protocol, WalletConnect and viem, none of which
 * run under jsdom". Two of those four are true. EIP-6963 is nothing but
 * `CustomEvent` on `window`, which jsdom implements; the other two arrive
 * through dynamic `import()`, which jest can mock. So the discovery protocol
 * is exercised for real here and only the two libraries are faked.
 *
 * The case worth having is the deduplication: a wallet that announces twice —
 * which is ordinary, since the request event can be answered by an extension
 * that also replays on load — must not produce two identical buttons.
 */

const EthereumProviderInit = jest.fn();
jest.mock(
  "@walletconnect/ethereum-provider",
  () => ({ EthereumProvider: { init: (...a: unknown[]) => EthereumProviderInit(...a) } }),
  { virtual: true }
);

const signMessage = jest.fn();
const createWalletClient = jest.fn(() => ({ signMessage }));
const custom = jest.fn((p: unknown) => ({ __transport: p }));
jest.mock(
  "viem",
  () => ({
    createWalletClient: (...a: unknown[]) => createWalletClient(...a),
    custom: (...a: unknown[]) => custom(...a),
  }),
  { virtual: true }
);

import {
  discoverInjectedConnectors,
  walletConnectConnector,
  getDefaultConnectors,
  defaultEvmSigner,
} from "./evmConnectors";

/** Announce one EIP-6963 provider, as an extension would. */
function announce(rdns: string, uuid = rdns, provider: unknown = {}) {
  window.dispatchEvent(
    new CustomEvent("eip6963:announceProvider", {
      detail: { info: { uuid, name: rdns.toUpperCase(), icon: "i.svg", rdns }, provider },
    })
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

/** Start discovery, let announcements land, then run out the window. */
async function discover(during: () => void, timeoutMs?: number) {
  const pending = discoverInjectedConnectors(timeoutMs);
  during();
  jest.runAllTimers();
  return pending;
}

describe("discoverInjectedConnectors", () => {
  it("resolves empty when nothing announces", async () => {
    await expect(discover(() => {})).resolves.toEqual([]);
  });

  it("returns one connector per announced wallet", async () => {
    const connectors = await discover(() => {
      announce("io.metamask");
      announce("com.coinbase");
    });

    expect(connectors.map((c) => c.id)).toEqual(["io.metamask", "com.coinbase"]);
    expect(connectors[0].name).toBe("IO.METAMASK");
    expect(connectors[0].icon).toBe("i.svg");
  });

  it("ignores a wallet that announces twice", async () => {
    const connectors = await discover(() => {
      announce("io.metamask");
      announce("io.metamask");
    });
    expect(connectors).toHaveLength(1);
  });

  it("treats the same rdns under a different uuid as a second wallet", async () => {
    // The uuid is what the protocol says is unique, so that is what is
    // deduplicated on, even though the rdns looks like the identity.
    const connectors = await discover(() => {
      announce("io.metamask", "uuid-a");
      announce("io.metamask", "uuid-b");
    });
    expect(connectors).toHaveLength(2);
  });

  it("ignores an announcement with no uuid", async () => {
    const connectors = await discover(() => {
      window.dispatchEvent(
        new CustomEvent("eip6963:announceProvider", { detail: { info: {} } })
      );
    });
    expect(connectors).toEqual([]);
  });

  it("ignores an announcement with no detail at all", async () => {
    const connectors = await discover(() => {
      window.dispatchEvent(new CustomEvent("eip6963:announceProvider"));
    });
    expect(connectors).toEqual([]);
  });

  it("stops listening once the window closes", async () => {
    const connectors = await discover(() => announce("io.metamask"));
    announce("com.coinbase");
    jest.runAllTimers();
    expect(connectors).toHaveLength(1);
  });

  it("asks for providers by dispatching the request event", async () => {
    const seen = jest.fn();
    window.addEventListener("eip6963:requestProvider", seen);
    await discover(() => {});
    expect(seen).toHaveBeenCalled();
    window.removeEventListener("eip6963:requestProvider", seen);
  });

  it("honours a custom collection window", async () => {
    const pending = discoverInjectedConnectors(50);
    announce("io.metamask");
    jest.advanceTimersByTime(49);
    jest.advanceTimersByTime(1);
    await expect(pending).resolves.toHaveLength(1);
  });

  describe("the connector it builds", () => {
    it("connects and returns the first account", async () => {
      const request = jest.fn().mockResolvedValue(["0xabc", "0xdef"]);
      const [connector] = await discover(() =>
        announce("io.metamask", "u", { request })
      );

      await expect(connector.connect()).resolves.toEqual({
        provider: { request },
        address: "0xabc",
      });
      expect(request).toHaveBeenCalledWith({ method: "eth_requestAccounts" });
    });

    it("returns an empty address when the wallet grants no accounts", async () => {
      const request = jest.fn().mockResolvedValue([]);
      const [connector] = await discover(() =>
        announce("io.metamask", "u", { request })
      );
      await expect(connector.connect()).resolves.toMatchObject({ address: "" });
    });

    it("returns an empty address when the wallet answers with nothing", async () => {
      const request = jest.fn().mockResolvedValue(null);
      const [connector] = await discover(() =>
        announce("io.metamask", "u", { request })
      );
      await expect(connector.connect()).resolves.toMatchObject({ address: "" });
    });
  });
});

describe("walletConnectConnector", () => {
  it("is offered without loading the provider library", () => {
    const connector = walletConnectConnector("pid-1");
    expect(connector).toMatchObject({
      id: "walletconnect",
      name: "WalletConnect",
    });
    // The lazy import is the point: nothing loads until the user picks it.
    expect(EthereumProviderInit).not.toHaveBeenCalled();
  });

  it("opens the modal and returns the connected account", async () => {
    const provider = {
      connect: jest.fn().mockResolvedValue(undefined),
      request: jest.fn().mockResolvedValue(["0xwc"]),
    };
    EthereumProviderInit.mockResolvedValue(provider);

    await expect(walletConnectConnector("pid-1").connect()).resolves.toEqual({
      provider,
      address: "0xwc",
    });
    expect(EthereumProviderInit).toHaveBeenCalledWith({
      projectId: "pid-1",
      chains: [1],
      optionalChains: [1],
      showQrModal: true,
    });
    expect(provider.request).toHaveBeenCalledWith({ method: "eth_accounts" });
  });

  it("returns an empty address when the session grants no accounts", async () => {
    EthereumProviderInit.mockResolvedValue({
      connect: jest.fn(),
      request: jest.fn().mockResolvedValue(undefined),
    });
    await expect(
      walletConnectConnector("pid").connect()
    ).resolves.toMatchObject({ address: "" });
  });
});

describe("getDefaultConnectors", () => {
  it("appends WalletConnect when a project id is configured", async () => {
    const pending = getDefaultConnectors("pid-1");
    announce("io.metamask");
    jest.runAllTimers();

    const connectors = await pending;
    expect(connectors.map((c) => c.id)).toEqual([
      "io.metamask",
      "walletconnect",
    ]);
  });

  it("offers injected wallets only when no project id is configured", async () => {
    const pending = getDefaultConnectors("");
    announce("io.metamask");
    jest.runAllTimers();

    await expect(pending).resolves.toHaveLength(1);
  });
});

describe("defaultEvmSigner", () => {
  it("personal_signs the challenge through viem", async () => {
    signMessage.mockResolvedValue("0xsignature");
    const provider = { request: jest.fn() };

    await expect(
      defaultEvmSigner(provider as never, "0xabc", "challenge")
    ).resolves.toBe("0xsignature");

    expect(custom).toHaveBeenCalledWith(provider);
    expect(createWalletClient).toHaveBeenCalledWith({
      transport: { __transport: provider },
    });
    expect(signMessage).toHaveBeenCalledWith({
      account: "0xabc",
      message: "challenge",
    });
  });
});
