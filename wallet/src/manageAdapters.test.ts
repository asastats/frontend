/**
 * @jest-environment jsdom
 */

/**
 * The step-up signers, which are what stand between "somebody clicked" and a
 * privilege-expanding change to an account.
 *
 * The rule worth testing is the same on both chains and stated in
 * {@link StepUpSigner}: **the connected account must be the primary**, or the
 * step-up can be met by any key the user happens to have connected. Each chain
 * has its own way of getting that wrong, so each gets its own refusal case.
 *
 * `algorandManager` memoises its WalletManager in module scope, so the suite
 * re-imports through `jest.isolateModulesAsync` wherever that cache is part of
 * what is being tested.
 */

const walletManagerCtor = jest.fn();
jest.mock("@txnlab/use-wallet", () => ({
  WalletId: { PERA: "pera" },
  WalletManager: function (this: any, ...args: unknown[]) {
    return walletManagerCtor(...args);
  },
}));

jest.mock("algosdk", () => ({
  makePaymentTxnWithSuggestedParamsFromObject: jest.fn((fields) => ({
    ...fields,
    __txn: true,
  })),
  encodeUnsignedTransaction: jest.fn(() => Uint8Array.from([1, 2, 3])),
}));

const getDefaultConnectors = jest.fn();
const defaultEvmSigner = jest.fn();
jest.mock("./evmConnectors", () => ({
  getDefaultConnectors: (...a: unknown[]) => getDefaultConnectors(...a),
  defaultEvmSigner: (...a: unknown[]) => defaultEvmSigner(...a),
}));

import { buildStepUpSign } from "./manageAdapters";
import {
  makePaymentTxnWithSuggestedParamsFromObject,
  encodeUnsignedTransaction,
} from "algosdk";

const PRIMARY = "0x52908400098527886E0F7030069857D2E4169EE7";
const ALGO = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M";

/** A fake WalletManager whose `wallets` list the signer searches. */
function manager(wallets: unknown[] = []) {
  return {
    wallets,
    resumeSessions: jest.fn().mockResolvedValue(undefined),
    algodClient: {
      getTransactionParams: () => ({
        do: jest.fn().mockResolvedValue({ fee: 1000 }),
      }),
    },
  };
}

/** A connected Algorand wallet whose active account is `address`. */
function algoWallet(address: string, signed: (Uint8Array | null)[]) {
  return {
    isConnected: true,
    activeAccount: { address },
    signTransactions: jest.fn().mockResolvedValue(signed),
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  (global.fetch as jest.Mock).mockReset();
});

describe("chain dispatch", () => {
  it("refuses a chain it does not know", async () => {
    const sign = buildStepUpSign({ apiBase: "/api", wcProjectId: "" });
    await expect(sign(PRIMARY, "solana", "msg")).rejects.toThrow(
      "Unsupported chain: solana"
    );
  });

  it("routes algorand to the injected override when one is given", async () => {
    const algorandStepUpSign = jest
      .fn()
      .mockResolvedValue({ signedTransaction: "sig" });
    const sign = buildStepUpSign({
      apiBase: "/api",
      wcProjectId: "",
      algorandStepUpSign,
    });

    await expect(sign(ALGO, "algorand", "message")).resolves.toEqual({
      signedTransaction: "sig",
    });
    expect(algorandStepUpSign).toHaveBeenCalledWith(ALGO, "message");
  });
});

describe("the EVM signer", () => {
  it("signs when the connected wallet is the primary", async () => {
    const provider = { request: jest.fn() };
    getDefaultConnectors.mockResolvedValue([
      { connect: jest.fn().mockResolvedValue({ provider, address: PRIMARY }) },
    ]);
    defaultEvmSigner.mockResolvedValue("0xsignature");

    const sign = buildStepUpSign({ apiBase: "/api", wcProjectId: "pid" });
    await expect(sign(PRIMARY, "evm", "challenge")).resolves.toEqual({
      signature: "0xsignature",
    });
    expect(getDefaultConnectors).toHaveBeenCalledWith("pid");
    expect(defaultEvmSigner).toHaveBeenCalledWith(provider, PRIMARY, "challenge");
  });

  it("compares addresses case-insensitively", async () => {
    // EIP-55 checksummed and all-lowercase are the same account, and a wallet
    // may return either. Refusing on case would refuse the legitimate user.
    getDefaultConnectors.mockResolvedValue([
      {
        connect: jest
          .fn()
          .mockResolvedValue({ provider: {}, address: PRIMARY.toLowerCase() }),
      },
    ]);
    defaultEvmSigner.mockResolvedValue("0xsig");
    const sign = buildStepUpSign({ apiBase: "/api", wcProjectId: "" });
    await expect(sign(PRIMARY, "evm", "m")).resolves.toEqual({
      signature: "0xsig",
    });
  });

  it("refuses when the connected wallet is a different account", async () => {
    getDefaultConnectors.mockResolvedValue([
      {
        connect: jest
          .fn()
          .mockResolvedValue({ provider: {}, address: "0xsomeoneelse" }),
      },
    ]);
    const sign = buildStepUpSign({ apiBase: "/api", wcProjectId: "" });
    await expect(sign(PRIMARY, "evm", "m")).rejects.toThrow(
      "Connected wallet is not your primary address"
    );
    expect(defaultEvmSigner).not.toHaveBeenCalled();
  });

  it("refuses when the wallet returns no address", async () => {
    getDefaultConnectors.mockResolvedValue([
      { connect: jest.fn().mockResolvedValue({ provider: {}, address: "" }) },
    ]);
    const sign = buildStepUpSign({ apiBase: "/api", wcProjectId: "" });
    await expect(sign(PRIMARY, "evm", "m")).rejects.toThrow(
      "Connected wallet is not your primary address"
    );
  });

  it("reports having no EVM wallet at all", async () => {
    getDefaultConnectors.mockResolvedValue([]);
    const sign = buildStepUpSign({ apiBase: "/api", wcProjectId: "" });
    await expect(sign(PRIMARY, "evm", "m")).rejects.toThrow(
      "No EVM wallet available"
    );
  });
});

describe("the Algorand signer", () => {
  /** Import a fresh module so the memoised WalletManager starts empty. */
  async function fresh() {
    let built!: typeof buildStepUpSign;
    await jest.isolateModulesAsync(async () => {
      ({ buildStepUpSign: built } = await import("./manageAdapters"));
    });
    return built;
  }

  /** Build a signer over a fresh module with `wallets` connected. */
  async function signerFor(wallets: unknown[], ok = true) {
    walletManagerCtor.mockReturnValue(manager(wallets));
    (global.fetch as jest.Mock).mockResolvedValue({
      ok,
      json: async () => [{ id: "pera" }],
    });
    const build = await fresh();
    return build({ apiBase: "/api", wcProjectId: "" });
  }

  it("signs a zero-amount self payment carrying the challenge as its note", async () => {
    const wallet = algoWallet(ALGO, [Uint8Array.from([9, 9])]);
    const sign = await signerFor([wallet]);

    await expect(sign(ALGO, "algorand", "challenge")).resolves.toEqual({
      signedTransaction: btoa(String.fromCharCode(9, 9)),
    });

    // A self-payment of zero is the cheapest thing that carries a signature and
    // moves nothing; the challenge rides in the note.
    const fields = (makePaymentTxnWithSuggestedParamsFromObject as jest.Mock)
      .mock.calls[0][0];
    expect(fields.sender).toBe(ALGO);
    expect(fields.receiver).toBe(ALGO);
    expect(fields.amount).toBe(0);
    expect(new TextDecoder().decode(fields.note)).toBe("challenge");
    expect(encodeUnsignedTransaction).toHaveBeenCalled();
    expect(wallet.signTransactions).toHaveBeenCalledWith([
      Uint8Array.from([1, 2, 3]),
    ]);
  });

  it("reuses the manager on a second call rather than refetching wallets", async () => {
    const sign = await signerFor([algoWallet(ALGO, [Uint8Array.from([1])])]);
    await sign(ALGO, "algorand", "one");
    await sign(ALGO, "algorand", "two");

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(walletManagerCtor).toHaveBeenCalledTimes(1);
  });

  it("reports a wallets list that could not be loaded", async () => {
    const sign = await signerFor([], false);
    await expect(sign(ALGO, "algorand", "m")).rejects.toThrow(
      "Failed to load supported wallets"
    );
  });

  it("refuses when the primary is not the active account", async () => {
    // The Algorand form of the same rule the EVM path enforces: being
    // connected is not enough, it must be *this* account.
    const sign = await signerFor([algoWallet("SOMEBODYELSE", [])]);
    await expect(sign(ALGO, "algorand", "m")).rejects.toThrow(
      "Connect your primary Algorand wallet"
    );
  });

  it("refuses when the wallet is the primary but not connected", async () => {
    const sign = await signerFor([
      { isConnected: false, activeAccount: { address: ALGO } },
    ]);
    await expect(sign(ALGO, "algorand", "m")).rejects.toThrow(
      "Connect your primary Algorand wallet"
    );
  });

  it("reports a wallet that returned nothing for the signature", async () => {
    const sign = await signerFor([algoWallet(ALGO, [null])]);
    await expect(sign(ALGO, "algorand", "m")).rejects.toThrow(
      "No signed transaction returned"
    );
  });
});
