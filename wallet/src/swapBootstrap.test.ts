/**
 * @jest-environment jsdom
 */

/**
 * The swap bridge's wiring: what `window.asastatsSwap` is built from.
 *
 * This module carried `/* istanbul ignore file *\/` on the grounds that it is
 * "browser/wallet/algod glue" whose orchestration is tested in
 * `swapBridge.test`. That was true of most of it and not of `buildDeps`, which
 * is where every algod shape quirk lives — the `min-balance` / `minBalance`
 * spelling, the `txid` / `txId` spelling, the 404-means-not-opted-in read.
 * Each of those is a silent wrong answer rather than a crash if it regresses,
 * and none is exercised by `swapBridge.test`, which receives `deps` already
 * built.
 *
 * `swapManager` memoises in module scope, so every test imports fresh.
 */

const walletManagerCtor = jest.fn();
jest.mock("@txnlab/use-wallet", () => {
  const actual = jest.requireActual("@txnlab/use-wallet");
  return {
    ...actual,
    WalletManager: function (this: any, ...args: unknown[]) {
      return walletManagerCtor(...args);
    },
  };
});

const encodeUnsignedTransaction = jest.fn((t: unknown) => ({ encoded: t }));
const algoWaitForConfirmation = jest.fn().mockResolvedValue(undefined);
const makeAssetTransferTxn = jest.fn(() => ({
  toByte: () => Uint8Array.from([1, 1]),
}));
jest.mock("algosdk", () => {
  const actual = jest.requireActual("algosdk");
  return {
    ...actual,
    encodeUnsignedTransaction: (...a: unknown[]) => encodeUnsignedTransaction(...a),
    waitForConfirmation: (...a: unknown[]) => algoWaitForConfirmation(...a),
    makeAssetTransferTxnWithSuggestedParamsFromObject: (...a: unknown[]) =>
      makeAssetTransferTxn(...a),
  };
});

const signAndSend = jest.fn().mockResolvedValue("SENT");
const signAndSendPartial = jest.fn().mockResolvedValue("PARTIAL");
const optIn = jest.fn().mockResolvedValue("OPTED");
const assetCreator = jest.fn().mockResolvedValue("CREATOR");
jest.mock("./swapBridge", () => ({
  signAndSend: (...a: unknown[]) => signAndSend(...a),
  signAndSendPartial: (...a: unknown[]) => signAndSendPartial(...a),
  optIn: (...a: unknown[]) => optIn(...a),
  assetCreator: (...a: unknown[]) => assetCreator(...a),
}));

const ADDRESS = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M";

/** algod stub whose every method is overridable per test. */
function algod(overrides: Record<string, unknown> = {}) {
  return {
    getTransactionParams: () => ({ do: jest.fn().mockResolvedValue({ fee: 1 }) }),
    accountAssetInformation: () => ({ do: jest.fn().mockResolvedValue({}) }),
    accountInformation: () => ({ do: jest.fn().mockResolvedValue({ amount: 0 }) }),
    sendRawTransaction: () => ({ do: jest.fn().mockResolvedValue({ txid: "T" }) }),
    getAssetByID: jest.fn(() => ({ do: jest.fn().mockResolvedValue({}) })),
    ...overrides,
  };
}

/** A connected wallet with an active account. */
function connected(address: string | null = ADDRESS) {
  return {
    isConnected: true,
    activeAccount: address ? { address } : null,
    signTransactions: jest.fn().mockResolvedValue([Uint8Array.from([9])]),
  };
}

/** Import fresh (the manager cache is module state) and run initSwapBridge. */
async function boot({
  wallets = [connected()],
  client = algod(),
  ok = true,
  markup = '<div id="id-swap-swap"></div>',
  signer = "SIGNER_FN" as unknown,
}: {
  wallets?: unknown[];
  /**
   * The algod client, or a function installed as a *getter* for it --
   * use-wallet publishes `algodClient` as one, so it is a place the swap half
   * can throw while the wallet half has already succeeded.
   */
  client?: ReturnType<typeof algod> | (() => unknown);
  ok?: boolean;
  markup?: string;
  /**
   * What `manager.transactionSigner` yields. A function is installed as a
   * *getter*, which is what use-wallet actually publishes -- and it throws
   * `No active wallet found!` when nothing is active. Reading it eagerly
   * therefore takes the whole bridge down, which no test could see while this
   * was a plain string that cannot throw.
   */
  signer?: unknown;
} = {}) {
  document.body.innerHTML = markup;
  const manager = {
    wallets,
    algodClient: client,
    resumeSessions: jest.fn().mockResolvedValue(undefined),
  };
  if (typeof signer === "function") {
    Object.defineProperty(manager, "transactionSigner", {
      get: signer as () => unknown,
      configurable: true,
    });
  } else {
    (manager as Record<string, unknown>).transactionSigner = signer;
  }
  if (typeof client === "function") {
    Object.defineProperty(manager, "algodClient", {
      get: client as () => unknown,
      configurable: true,
    });
  }
  walletManagerCtor.mockReturnValue(manager);
  (global.fetch as jest.Mock).mockResolvedValue({
    ok,
    json: async () => [{ id: "pera" }],
  });

  let init!: (doc?: Document) => Promise<void>;
  await jest.isolateModulesAsync(async () => {
    ({ initSwapBridge: init } = await import("./swapBootstrap"));
  });
  await init(document);
  return {
    manager,
    bridge: (window as any).asastatsSwap,
    wallet: (window as any).asastatsWallet,
    init,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  delete (window as any).asastatsSwap;
  delete (window as any).asastatsWallet;
  (global.fetch as jest.Mock).mockReset();
});

describe("mounting", () => {
  it("no-ops without any entry point", async () => {
    const { bridge, wallet } = await boot({ markup: "<div></div>" });
    expect(bridge).toBeUndefined();
    expect(wallet).toBeUndefined();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("mounts on the accordion container", async () => {
    expect((await boot()).bridge).toBeDefined();
  });

  it("mounts on the per-ASA modal marker", async () => {
    const { bridge } = await boot({
      markup: '<div id="id-swap-enabled"></div>',
    });
    expect(bridge).toBeDefined();
  });

  it("reads the API base from the container", async () => {
    await boot({
      markup: '<div id="id-swap-swap" data-api-base="/custom"></div>',
    });
    expect(global.fetch).toHaveBeenCalledWith("/custom/wallets/");
  });

  it("falls back to the default API base", async () => {
    await boot();
    expect(global.fetch).toHaveBeenCalledWith("/api/v2/wallet/wallets/");
  });

  it("announces itself so a widget that loaded first can re-render", async () => {
    document.body.innerHTML = '<div id="id-swap-swap"></div>';
    const heard = jest.fn();
    window.addEventListener("asastats:swap-ready", heard);
    await boot();
    expect(heard).toHaveBeenCalled();
    window.removeEventListener("asastats:swap-ready", heard);
  });

  it("publishes the wallet alongside the swap", async () => {
    const { wallet } = await boot();
    expect(wallet.activeAddress()).toBe(ADDRESS);
  });

  describe("a page carrying only the dust sweep", () => {
    /**
     * `_swap_entry.html` gates the sweep (`{% if dustsweep_address %}`) and the
     * swap (`{% if swap_url %}`) separately, so a reader can qualify for the
     * sweep on a page with no swap on it -- no router resolved, for instance.
     *
     * Mounting only for the swap's entries meant no wallet state was published
     * at all for that reader, and `dustsweep.js` hid its button forever with
     * nothing in the console to say why. The sweep needs a connected wallet;
     * it needs nothing else this module builds.
     */
    const SWEEP = '<div id="id-dustsweep"></div>';

    it("publishes wallet state", async () => {
      const { wallet } = await boot({ markup: SWEEP });
      expect(wallet.activeAddress()).toBe(ADDRESS);
    });

    it("announces the wallet", async () => {
      document.body.innerHTML = SWEEP;
      const heard = jest.fn();
      window.addEventListener("asastats:wallet-ready", heard);
      await boot({ markup: SWEEP });
      window.removeEventListener("asastats:wallet-ready", heard);
      expect(heard).toHaveBeenCalled();
    });

    it("builds the signing bridge too, because the sweep signs", async () => {
      /**
       * The sweep is a first-class caller of this bridge: `signAndSend`,
       * `signAndSendPartial` and `assetCreator` are all its. Publishing wallet
       * state without it would reveal the button and then tell a reader who
       * *has* connected to "Connect your wallet to sign this group", which is
       * `dustsweep.js`'s message when `window.asastatsSwap` is missing.
       */
      const { bridge } = await boot({ markup: SWEEP });
      expect(bridge).toBeDefined();
      expect(typeof bridge.signAndSend).toBe("function");
      expect(typeof bridge.assetCreator).toBe("function");
    });
  });

  describe("retrying after the swap half failed", () => {
    /**
     * The recovery the reported bug never got. A reader with no wallet
     * connected published wallet state and no bridge; the next htmx settle
     * calls this again, and it must finish the job rather than start over or
     * give up.
     *
     * This is also the only caller that reaches the memoised branch of
     * `swapManager` now: a page whose needs are already met returns before
     * asking for a manager at all.
     */
    function lateSigner() {
      const state = { active: false };
      return {
        state,
        get: () => {
          if (!state.active) throw new Error("No active wallet found!");
          return "SIGNER_FN";
        },
      };
    }

    it("reuses the manager and publishes the bridge once it can", async () => {
      const logged = jest.spyOn(console, "error").mockImplementation(() => {});
      const late = lateSigner();
      const { init, manager, wallet } = await boot({
        wallets: [],
        client: () => {
          throw new Error("no algod yet");
        },
      });

      expect(wallet).toBeDefined();
      expect((window as any).asastatsSwap).toBeUndefined();
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // the wallet connects, and the page settles again
      (manager as any).wallets = [connected()];
      Object.defineProperty(manager, "algodClient", {
        value: algod(),
        configurable: true,
      });
      Object.defineProperty(manager, "transactionSigner", {
        get: late.get,
        configurable: true,
      });
      late.state.active = true;
      await init(document);
      logged.mockRestore();

      expect((window as any).asastatsSwap).toBeDefined();
      expect((window as any).asastatsWallet.activeAddress()).toBe(ADDRESS);
      // memoised: the wallets list is fetched once, the sessions resumed again
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(manager.resumeSessions).toHaveBeenCalledTimes(2);
    });
  });

  describe("when the swap half fails", () => {
    it("logs against the swap and leaves the wallet up", async () => {
      /**
       * `buildDeps` reads `manager.algodClient`, which use-wallet publishes as
       * a getter. Anything that throws between the wallet being published and
       * the bridge being finished belongs to the swap, and must be reported as
       * the swap's -- without taking connection state down with it.
       */
      const logged = jest.spyOn(console, "error").mockImplementation(() => {});
      const { bridge, wallet } = await boot({
        client: () => {
          throw new Error("algod unavailable");
        },
      });

      expect(bridge).toBeUndefined();
      expect(wallet.activeAddress()).toBe(ADDRESS);
      expect(logged).toHaveBeenCalledWith(
        "Error initializing swap bridge:",
        expect.any(Error)
      );
      logged.mockRestore();
    });

    /**
     * The reason this split exists. A swap that cannot start must not take
     * wallet state with it -- that is what removed the Dust Sweep button for
     * readers with no wallet connected, and it would happen again for any
     * future breakage inside the swap's own construction.
     */
    it("leaves the wallet published", async () => {
      const logged = jest.spyOn(console, "error").mockImplementation(() => {});
      const { wallet, bridge } = await boot({
        wallets: [],
        signer: () => {
          throw new Error("No active wallet found!");
        },
      });
      logged.mockRestore();

      // The getter keeps the bridge up too; this asserts the independence
      // rather than that one fix, so it holds whatever breaks next.
      expect(wallet).toBeDefined();
      expect(wallet.activeAddress()).toBeNull();
      expect(bridge).toBeDefined();
    });
  });

  it("logs and publishes nothing when the wallets list fails", async () => {
    // A page that cannot reach the API must not leave a half-built bridge
    // behind for a widget to call into. Reported against the wallet rather
    // than the swap: without a manager neither half can be published, and a
    // page carrying only the sweep has no swap to blame.
    const logged = jest.spyOn(console, "error").mockImplementation(() => {});
    const { bridge, wallet } = await boot({ ok: false });
    expect(bridge).toBeUndefined();
    expect(wallet).toBeUndefined();
    expect(logged).toHaveBeenCalledWith(
      "Error connecting the wallet:",
      expect.any(Error)
    );
    logged.mockRestore();
  });

  it("reuses the manager on a second mount", async () => {
    document.body.innerHTML = '<div id="id-swap-swap"></div>';
    const manager = {
      wallets: [connected()],
      algodClient: algod(),
      transactionSigner: "S",
      resumeSessions: jest.fn().mockResolvedValue(undefined),
    };
    walletManagerCtor.mockReturnValue(manager);
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => [{ id: "pera" }],
    });

    await jest.isolateModulesAsync(async () => {
      const { initSwapBridge } = await import("./swapBootstrap");
      await initSwapBridge(document);
      await initSwapBridge(document);
    });

    // The second call finds this page's needs already met and returns before
    // touching the wallet at all. `main.ts` now calls this on *every* htmx
    // settle -- it can no longer ask "is the swap up?" itself, because a page
    // carrying only the sweep never publishes a swap -- so the cost of
    // re-entry is paid here.
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(manager.resumeSessions).toHaveBeenCalledTimes(1);
  });

  it("defaults to the global document", async () => {
    document.body.innerHTML = '<div id="id-swap-swap"></div>';
    walletManagerCtor.mockReturnValue({
      wallets: [connected()],
      algodClient: algod(),
      transactionSigner: "S",
      resumeSessions: jest.fn().mockResolvedValue(undefined),
    });
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => [{ id: "pera" }],
    });
    await jest.isolateModulesAsync(async () => {
      const { initSwapBridge } = await import("./swapBootstrap");
      await initSwapBridge();
    });
    expect((window as any).asastatsSwap).toBeDefined();
  });
});

describe("the published surface", () => {
  it("forwards each call to the tested bridge functions", async () => {
    const { bridge } = await boot();

    await expect(bridge.signAndSend([], { outputAssetId: 1 })).resolves.toBe(
      "SENT"
    );
    await expect(bridge.signAndSendPartial({})).resolves.toBe("PARTIAL");
    await expect(bridge.optIn(7)).resolves.toBe("OPTED");
    expect(bridge.signer).toBe("SIGNER_FN");
  });

  describe("when use-wallet has no active wallet", () => {
    /**
     * `manager.transactionSigner` is a *getter* in use-wallet, and it throws
     * `No active wallet found!` rather than returning null. Reading it while
     * building the published object therefore threw before the assignment, so
     * `window.asastatsSwap` was never created and the catch below turned a
     * dead bridge into a single console line.
     *
     * It cost a live feature: `dustsweep.js` reads `activeAddress()` off this
     * object to decide whether to show its button, and its polling recovery
     * cannot help because it polls a bridge that was never built. Users
     * reported the Dust Sweep button had vanished and not come back.
     *
     * The old harness set `transactionSigner` to a plain string, which cannot
     * throw -- so every test passed against a mock that supplied what
     * production could not.
     */
    const throwing = () => {
      throw new Error("No active wallet found!");
    };

    it("still publishes the bridge", async () => {
      const { bridge } = await boot({ wallets: [], signer: throwing });
      expect(bridge).toBeDefined();
      expect((window as any).asastatsSwap).toBe(bridge);
    });

    it("still answers activeAddress, which needs no active wallet", async () => {
      const { bridge } = await boot({ wallets: [], signer: throwing });
      expect(bridge.activeAddress()).toBeNull();
    });

    it("still dispatches swap-ready", async () => {
      const heard = jest.fn();
      window.addEventListener("asastats:swap-ready", heard);
      await boot({ wallets: [], signer: throwing });
      window.removeEventListener("asastats:swap-ready", heard);
      expect(heard).toHaveBeenCalled();
    });

    it("raises the wallet's own error only when signer is read", async () => {
      /** Deferred, not swallowed: a caller still gets the real reason. */
      const { bridge } = await boot({ wallets: [], signer: throwing });
      expect(() => bridge.signer).toThrow("No active wallet found!");
    });

    it("reads the signer afresh, so connecting a wallet later works", async () => {
      let active = false;
      const { bridge } = await boot({
        wallets: [],
        signer: () => {
          if (!active) throw new Error("No active wallet found!");
          return "SIGNER_FN";
        },
      });

      expect(() => bridge.signer).toThrow("No active wallet found!");
      active = true;
      expect(bridge.signer).toBe("SIGNER_FN");
    });
  });

  it("reads an asset creator through algod, for the sweep's forfeit check", async () => {
    const asset = { params: { creator: "C" } };
    const getAssetByID = jest.fn(() => ({
      do: jest.fn().mockResolvedValue(asset),
    }));
    const { bridge } = await boot({ client: algod({ getAssetByID }) });

    await expect(bridge.assetCreator(31566704)).resolves.toBe("CREATOR");
    const [assetId, deps] = assetCreator.mock.calls[0] as [number, any];
    expect(assetId).toBe(31566704);
    await expect(deps.getAsset(31566704)).resolves.toBe(asset);
    expect(getAssetByID).toHaveBeenCalledWith(31566704);
  });
});

describe("activeAddress", () => {
  it("returns the connected account", async () => {
    expect((await boot()).bridge.activeAddress()).toBe(ADDRESS);
  });

  it("is null with no wallet connected", async () => {
    expect((await boot({ wallets: [] })).bridge.activeAddress()).toBeNull();
  });

  it("is null when a wallet is connected without an active account", async () => {
    const { bridge } = await boot({
      wallets: [{ isConnected: true, activeAccount: null }],
    });
    expect(bridge.activeAddress()).toBeNull();
  });

  it("skips a wallet that is not connected", async () => {
    const { bridge } = await boot({
      wallets: [
        { isConnected: false, activeAccount: { address: "STALE" } },
        connected(),
      ],
    });
    expect(bridge.activeAddress()).toBe(ADDRESS);
  });
});

describe("the deps handed to the bridge", () => {
  /** Mount and return the `deps` object signAndSend was called with. */
  async function deps(options?: Parameters<typeof boot>[0]) {
    const { bridge, manager } = await boot(options);
    await bridge.signAndSend([], {});
    return { deps: signAndSend.mock.calls[0][1] as any, manager };
  }

  it("signTransactions forwards the whole group plus the indexes", async () => {
    // Pera verifies group integrity across every transaction, so sending only
    // the wallet-signed subset makes it reject with "Missing transaction(s)".
    const wallet = connected();
    const { deps: d } = await deps({ wallets: [wallet] });
    const group = [Uint8Array.from([1]), Uint8Array.from([2])];

    await d.signTransactions(group, [1]);
    expect(wallet.signTransactions).toHaveBeenCalledWith(group, [1]);
  });

  it("signTransactions refuses with no wallet connected", async () => {
    const { deps: d } = await deps({ wallets: [] });
    expect(() => d.signTransactions([], [])).toThrow(
      "Connect your Algorand wallet"
    );
  });

  it("isOptedIn is true when algod answers", async () => {
    const { deps: d } = await deps();
    await expect(d.isOptedIn(ADDRESS, 1)).resolves.toBe(true);
  });

  it("isOptedIn is false on the 404 that means not opted in", async () => {
    const { deps: d } = await deps({
      client: algod({
        accountAssetInformation: () => ({
          do: jest.fn().mockRejectedValue(new Error("404")),
        }),
      }),
    });
    await expect(d.isOptedIn(ADDRESS, 1)).resolves.toBe(false);
  });

  it("availableMicroAlgos subtracts the hyphenated min-balance", async () => {
    const { deps: d } = await deps({
      client: algod({
        accountInformation: () => ({
          do: jest
            .fn()
            .mockResolvedValue({ amount: 5_000_000, "min-balance": 1_000_000 }),
        }),
      }),
    });
    await expect(d.availableMicroAlgos(ADDRESS)).resolves.toBe(4_000_000n);
  });

  it("availableMicroAlgos accepts the camelCase spelling too", async () => {
    const { deps: d } = await deps({
      client: algod({
        accountInformation: () => ({
          do: jest
            .fn()
            .mockResolvedValue({ amount: 5_000_000, minBalance: 2_000_000 }),
        }),
      }),
    });
    await expect(d.availableMicroAlgos(ADDRESS)).resolves.toBe(3_000_000n);
  });

  it("availableMicroAlgos treats a missing min-balance as zero", async () => {
    const { deps: d } = await deps({
      client: algod({
        accountInformation: () => ({
          do: jest.fn().mockResolvedValue({ amount: 7 }),
        }),
      }),
    });
    await expect(d.availableMicroAlgos(ADDRESS)).resolves.toBe(7n);
  });

  it("submit reads the v3 txid", async () => {
    const { deps: d } = await deps();
    await expect(d.submit([])).resolves.toBe("T");
  });

  it("submit tolerates the older txId spelling", async () => {
    const { deps: d } = await deps({
      client: algod({
        sendRawTransaction: () => ({
          do: jest.fn().mockResolvedValue({ txId: "OLD" }),
        }),
      }),
    });
    await expect(d.submit([])).resolves.toBe("OLD");
  });

  it("submit returns an empty id when the node names neither", async () => {
    const { deps: d } = await deps({
      client: algod({
        sendRawTransaction: () => ({ do: jest.fn().mockResolvedValue({}) }),
      }),
    });
    await expect(d.submit([])).resolves.toBe("");
  });

  it("suggestedParams comes from algod", async () => {
    const { deps: d } = await deps();
    await expect(d.suggestedParams()).resolves.toEqual({ fee: 1 });
  });

  it("waitForConfirmation polls algosdk for a bounded number of rounds", async () => {
    const { deps: d, manager } = await deps();
    await d.waitForConfirmation("TXID");
    expect(algoWaitForConfirmation).toHaveBeenCalledWith(
      manager.algodClient,
      "TXID",
      6
    );
  });

  it("buildOptIn builds a zero-amount self transfer", async () => {
    const { deps: d } = await deps();
    const built = await d.buildOptIn(31566704);

    expect(makeAssetTransferTxn).toHaveBeenCalledWith({
      sender: ADDRESS,
      receiver: ADDRESS,
      amount: 0,
      assetIndex: 31566704,
      suggestedParams: { fee: 1 },
    });
    expect(built).toEqual([Uint8Array.from([1, 1])]);
  });

  it("buildOptIn refuses with no wallet connected", async () => {
    const { deps: d } = await deps({ wallets: [] });
    await expect(d.buildOptIn(1)).rejects.toThrow(
      "Connect your Algorand wallet"
    );
  });
});

describe("haystackSigner", () => {
  it("encodes each Transaction before handing it to the wallet", async () => {
    // Transaction objects cannot cross the bundle boundary safely — use-wallet
    // re-encodes them with its own class and overreads the DataView. Bytes can.
    const wallet = connected();
    const { bridge } = await boot({ wallets: [wallet] });
    const txns = [{ id: "a" }, { id: "b" }];

    await bridge.haystackSigner(txns as never, [0]);

    expect(encodeUnsignedTransaction).toHaveBeenCalledTimes(2);
    expect(wallet.signTransactions).toHaveBeenCalledWith(
      [{ encoded: txns[0] }, { encoded: txns[1] }],
      [0]
    );
  });

  it("refuses with no wallet connected", async () => {
    const { bridge } = await boot({ wallets: [] });
    expect(() => bridge.haystackSigner([], [])).toThrow(
      "Connect your Algorand wallet"
    );
  });
});
