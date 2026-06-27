import {
  optIn,
  signAndSend,
  type OptInDeps,
  type SignAndSendDeps,
  type SwapOpts,
} from "./swapBridge";

// ---------------------------------------------------------------------------
// Minimal algosdk mocks — kept in-module so the test file needs no jest config
// ---------------------------------------------------------------------------

// We mock the entire algosdk module so swapBridge.ts never touches real crypto.
jest.mock("algosdk", () => {
  const makeAssetTransferTxnWithSuggestedParamsFromObject = jest.fn(
    ({ sender, assetIndex }: any) => ({
      sender,
      assetIndex,
      group: undefined as any,
    }),
  );
  const makePaymentTxnWithSuggestedParamsFromObject = jest.fn(
    ({ sender, receiver, amount }: any) => ({
      sender,
      receiver,
      amount,
      group: undefined as any,
    }),
  );
  const decodeUnsignedTransaction = jest.fn((b: Uint8Array) => ({
    _raw: b,
    group: undefined as any,
  }));
  const encodeUnsignedTransaction = jest.fn((txn: any) =>
    txn._raw ?? new Uint8Array([0]),
  );
  const assignGroupID = jest.fn((txns: any[]) => {
    txns.forEach((t) => (t.group = new Uint8Array([99])));
  });
  const signLogicSigTransactionObject = jest.fn((_txn: any, _lsig: any) => ({
    blob: new Uint8Array([55]),
  }));
  return {
    makeAssetTransferTxnWithSuggestedParamsFromObject,
    makePaymentTxnWithSuggestedParamsFromObject,
    decodeUnsignedTransaction,
    encodeUnsignedTransaction,
    assignGroupID,
    signLogicSigTransactionObject,
  };
});

// Mock @folks-router/js-sdk
const MOCK_ESCROW = "ESCROW_ADDRESS_AAAA";
const mockLsig = {
  address: () => ({ toString: () => MOCK_ESCROW }),
};
const getReferrerLogicSig = jest.fn(() => mockLsig);
const prepareReferrerOptIntoAsset = jest.fn(
  (_sender: string, _referrer: string, _assetId: number, _sp: any) => [
    { unsignedTxn: new Uint8Array([71]), lsig: null },
    { unsignedTxn: new Uint8Array([72]), lsig: mockLsig },
  ],
);
jest.mock("@folks-router/js-sdk", () => ({
  getReferrerLogicSig: (...args: any[]) => getReferrerLogicSig(...args),
  prepareReferrerOptIntoAsset: (...args: any[]) =>
    prepareReferrerOptIntoAsset(...args),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TXN_A = new Uint8Array([1, 2, 3]);
const TXN_B = new Uint8Array([4, 5, 6]);
const SIG_A = new Uint8Array([10]);
const SIG_B = new Uint8Array([20]);

const DEFAULT_SP = { fee: 1000, firstValid: 1, lastValid: 1001 };

const BASE_OPTS: SwapOpts = {
  outputAssetId: 31566704,
  userNeedsOptIn: false,
};

function deps(overrides: Partial<SignAndSendDeps> = {}): {
  d: SignAndSendDeps;
  calls: { signed?: Uint8Array[]; submitted?: Uint8Array[]; confirmed?: string };
} {
  const calls: any = {};
  const d: SignAndSendDeps = {
    activeAddress: jest.fn(() => "AAAA"),
    signTransactions: jest.fn(async (txns: Uint8Array[], indexesToSign: number[]) => {
      calls.signed = txns;
      // Return a full-group-length array (parallel to txns) with a blob at each
      // wallet-signed index and null everywhere else — matching use-wallet v4's
      // actual return shape.
      const blobs = [SIG_A, SIG_B, new Uint8Array([30])];
      return txns.map((_: unknown, i: number) => {
        const pos = indexesToSign.indexOf(i);
        return pos >= 0 ? blobs[pos] : null;
      });
    }),
    suggestedParams: jest.fn(async () => DEFAULT_SP),
    isOptedIn: jest.fn(async () => true),
    submit: jest.fn(async (signed: Uint8Array[]) => {
      calls.submitted = signed;
      return "TXID123";
    }),
    waitForConfirmation: jest.fn(async (txid: string) => {
      calls.confirmed = txid;
    }),
    ...overrides,
  };
  return { d, calls };
}

// ---------------------------------------------------------------------------
// signAndSend — basic flow
// ---------------------------------------------------------------------------

describe("signAndSend", () => {
  it("signs, submits and confirms in order and returns the txid", async () => {
    const { d, calls } = deps();
    const txid = await signAndSend([TXN_A, TXN_B], d, BASE_OPTS);

    expect(d.suggestedParams).toHaveBeenCalled();
    expect(d.submit).toHaveBeenCalled();
    expect(calls.confirmed).toBe("TXID123");
    expect(txid).toBe("TXID123");
  });

  it("throws on an empty group and signs nothing", async () => {
    const { d } = deps();
    await expect(signAndSend([], d, BASE_OPTS)).rejects.toThrow(
      "Empty transaction group",
    );
    expect(d.signTransactions).not.toHaveBeenCalled();
    expect(d.submit).not.toHaveBeenCalled();
  });

  it("throws when no wallet account is active and signs nothing", async () => {
    const { d } = deps({ activeAddress: jest.fn(() => null) });
    await expect(signAndSend([TXN_A], d, BASE_OPTS)).rejects.toThrow(
      "No active wallet account",
    );
    expect(d.signTransactions).not.toHaveBeenCalled();
    expect(d.submit).not.toHaveBeenCalled();
  });

  it("throws and does not submit when the wallet omits a required signature", async () => {
    const { d } = deps({
      // Return a full-group-length array with null at the wallet leg's position —
      // simulates a wallet that silently drops a signature rather than rejecting.
      // (use-wallet v4 returns null-padded full-group arrays, not compact arrays.)
      signTransactions: jest.fn(async (txns: Uint8Array[]) =>
        txns.map(() => null),
      ),
    });
    await expect(signAndSend([TXN_A], d, BASE_OPTS)).rejects.toThrow(
      "Wallet did not sign a required transaction",
    );
    expect(d.submit).not.toHaveBeenCalled();
  });

  it("propagates a signer rejection (user cancel) and does not submit", async () => {
    const { d } = deps({
      signTransactions: jest.fn().mockRejectedValue(new Error("user rejected")),
    });
    await expect(signAndSend([TXN_A], d, BASE_OPTS)).rejects.toThrow(
      "user rejected",
    );
    expect(d.submit).not.toHaveBeenCalled();
  });

  it("propagates a submit rejection and does not confirm", async () => {
    const { d } = deps({
      submit: jest.fn().mockRejectedValue(new Error("overspend")),
    });
    await expect(signAndSend([TXN_A], d, BASE_OPTS)).rejects.toThrow("overspend");
    expect(d.waitForConfirmation).not.toHaveBeenCalled();
  });

  it("propagates a confirmation failure", async () => {
    const { d } = deps({
      waitForConfirmation: jest
        .fn()
        .mockRejectedValue(new Error("rejected in block")),
    });
    await expect(signAndSend([TXN_A], d, BASE_OPTS)).rejects.toThrow(
      "rejected in block",
    );
  });
});

// ---------------------------------------------------------------------------
// signAndSend — opt-in and referrer legs (shape B)
// ---------------------------------------------------------------------------

describe("signAndSend — opt-in / referrer legs", () => {
  beforeEach(() => {
    getReferrerLogicSig.mockClear();
    prepareReferrerOptIntoAsset.mockClear();
  });

  it("prepends a user opt-in leg when userNeedsOptIn=true", async () => {
    const { makeAssetTransferTxnWithSuggestedParamsFromObject } =
      jest.requireMock("algosdk");
    makeAssetTransferTxnWithSuggestedParamsFromObject.mockClear();

    const { d } = deps();
    await signAndSend([TXN_A], d, {
      outputAssetId: 31566704,
      userNeedsOptIn: true,
    });

    // The user opt-in is a 0-amount self-transfer of the output asset.
    expect(makeAssetTransferTxnWithSuggestedParamsFromObject).toHaveBeenCalledWith(
      expect.objectContaining({
        sender: "AAAA",
        receiver: "AAAA",
        amount: 0,
        assetIndex: 31566704,
      }),
    );
    // Wallet receives the full 2-txn group and signs both (no lsig legs).
    const allTxns: Uint8Array[] = (d.signTransactions as jest.Mock).mock.calls[0][0];
    const indexesToSign: number[] = (d.signTransactions as jest.Mock).mock.calls[0][1];
    expect(allTxns).toHaveLength(2);
    expect(indexesToSign).toEqual([0, 1]);
  });

  it("(a) no opt-in legs when userNeedsOptIn=false and no referrer", async () => {
    const { d } = deps();
    await signAndSend([TXN_A], d, {
      outputAssetId: 31566704,
      userNeedsOptIn: false,
    });
    // Full group (1 txn) is sent to the wallet; wallet signs index [0].
    expect(d.signTransactions).toHaveBeenCalledWith(
      expect.arrayContaining([expect.any(Uint8Array)]),
      [0], // indexesToSign: only the swap txn, at position 0
    );
    const allTxns: Uint8Array[] = (d.signTransactions as jest.Mock).mock.calls[0][0];
    const indexesToSign: number[] = (d.signTransactions as jest.Mock).mock.calls[0][1];
    expect(allTxns).toHaveLength(1);   // full group size
    expect(indexesToSign).toHaveLength(1); // wallet signs 1 of 1
    expect(getReferrerLogicSig).not.toHaveBeenCalled();
  });

  it("(c) SDK pair when escrow is unfunded (available < MBR + 1000)", async () => {
    const { d } = deps({
      isOptedIn: jest.fn(async () => false),
    });

    await signAndSend([TXN_A], d, {
      outputAssetId: 31566704,
      userNeedsOptIn: false,
      referrer: "REFERRER_ADDR",
    });

    expect(prepareReferrerOptIntoAsset).toHaveBeenCalledWith(
      "AAAA",
      "REFERRER_ADDR",
      31566704,
      { ...DEFAULT_SP, flatFee: true }
    );
    // Wallet receives full 3-txn group: [user-fund(0), lsig-optin(1), swap(2)].
    // It signs only indexes [0, 2]; index 1 is the lsig leg (escrow-signed).
    const allTxns: Uint8Array[] = (d.signTransactions as jest.Mock).mock.calls[0][0];
    const indexesToSign: number[] = (d.signTransactions as jest.Mock).mock.calls[0][1];
    expect(allTxns).toHaveLength(3);        // full group size
    expect(indexesToSign).toEqual([0, 2]);  // user-fund + swap; skip lsig leg
  });

  it("(d) lsig legs signed via signLogicSigTransactionObject, wallet legs via signTransactions", async () => {
    const { d } = deps({
      isOptedIn: jest.fn(async () => false),
    });
    await signAndSend([TXN_A], d, {
      outputAssetId: 31566704,
      userNeedsOptIn: false,
      referrer: "REFERRER_ADDR",
    });
    const { signLogicSigTransactionObject } = jest.requireMock("algosdk");
    expect(signLogicSigTransactionObject).toHaveBeenCalledTimes(1);
    expect(signLogicSigTransactionObject).toHaveBeenCalledWith(
      expect.anything(),
      mockLsig,
    );
    // Confirm the lsig blob ends up in the submitted group
    const submitted: Uint8Array[] = (d.submit as jest.Mock).mock.calls[0][0];
    expect(submitted).toContainEqual(new Uint8Array([55])); // signLogicSigTransactionObject returns {blob: [55]}
  });
});

// ---------------------------------------------------------------------------
// optIn
// ---------------------------------------------------------------------------

const OPTIN_TXN = new Uint8Array([7, 7, 7]);

function optInDeps(overrides: Partial<OptInDeps> = {}): {
  d: OptInDeps;
  calls: { built?: number; signed?: Uint8Array[] };
} {
  const calls: any = {};
  const d: OptInDeps = {
    activeAddress: jest.fn(() => "AAAA"),
    buildOptIn: jest.fn(async (assetId: number) => {
      calls.built = assetId;
      return [OPTIN_TXN];
    }),
    signTransactions: jest.fn(async (txns: Uint8Array[], indexesToSign: number[]) => {
      calls.signed = txns;
      return txns.map((_: unknown, i: number) => indexesToSign.includes(i) ? SIG_A : null);
    }),
    suggestedParams: jest.fn(async () => DEFAULT_SP),
    isOptedIn: jest.fn(async () => true),
    submit: jest.fn(async () => "OPTINTXID"),
    waitForConfirmation: jest.fn(async () => { }),
    ...overrides,
  };
  return { d, calls };
}

describe("optIn", () => {
  it("builds the opt-in txn then signs, submits and confirms it", async () => {
    const { d, calls } = optInDeps();
    const txid = await optIn(31566704, d);

    expect(calls.built).toBe(31566704);
    expect(d.submit).toHaveBeenCalledTimes(1);
    expect(d.waitForConfirmation).toHaveBeenCalledWith("OPTINTXID");
    expect(txid).toBe("OPTINTXID");
  });

  it("propagates a build failure and signs nothing", async () => {
    const { d } = optInDeps({
      buildOptIn: jest.fn().mockRejectedValue(new Error("no params")),
    });
    await expect(optIn(1, d)).rejects.toThrow("no params");
    expect(d.signTransactions).not.toHaveBeenCalled();
  });

  it("propagates a user-cancelled signature and submits nothing", async () => {
    const { d } = optInDeps({
      signTransactions: jest.fn().mockRejectedValue(new Error("user rejected")),
    });
    await expect(optIn(1, d)).rejects.toThrow("user rejected");
    expect(d.submit).not.toHaveBeenCalled();
  });
});
