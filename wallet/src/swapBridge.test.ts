import {
  assetCreator,
  optIn,
  rescueDiagnosis,
  signAndSend,
  signAndSendPartial,
  type OptInDeps,
  type SignAndSendDeps,
  type PartialSignedGroup,
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
    group: new Uint8Array([99]),
    fee: 1000,
  }));
  // A signed transaction carries the whole transaction, group and fee
  // included - so a double that omits them cannot model the failure this
  // module exists to catch, where a wallet hands back something *different*
  // from what it was given. Tests that need that override this.
  const decodeSignedTransaction = jest.fn((b: Uint8Array) => ({
    txn: { _raw: b.slice(0, 3), group: new Uint8Array([99]), fee: 1000 },
    sig: b.slice(3),
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
    decodeSignedTransaction,
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
// A signed transaction carries the transaction it signed, so these are the
// unsigned bytes with a signature byte appended - which is what the algosdk
// mock's `decodeSignedTransaction` splits back apart. Opaque one-byte blobs
// modelled a wallet returning something that re-encodes to neither what it
// was given nor anything else, and the consistency check rightly rejected it.
const TXN_C = new Uint8Array([7, 8, 9]);
const SIG_A = new Uint8Array([...TXN_A, 10]);
const SIG_B = new Uint8Array([...TXN_B, 20]);
// a third signature byte, so a decoder double can tell the three apart
const SIG_C = new Uint8Array([...TXN_C, 30]);

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

describe("signAndSendPartial", () => {
  function partial(): PartialSignedGroup {
    return {
      transactions: [TXN_A, TXN_B],
      signedTransactions: { "1": new Uint8Array([4, 5, 6, 20]) },
      quoteSignerIndex: 1,
    };
  }

  it("preserves the backend signature and asks the wallet for only user legs", async () => {
    const { d, calls } = deps();
    const txid = await signAndSendPartial(partial(), d);

    expect(d.signTransactions).toHaveBeenCalledWith([TXN_A, TXN_B], [0]);
    expect(calls.submitted).toEqual([SIG_A, new Uint8Array([4, 5, 6, 20])]);
    expect(txid).toBe("TXID123");
  });

  /**
   * Make the wallet's returned transaction differ from the one it was handed.
   *
   * Keyed on the blob rather than on call order: `decodeSignedTransaction`
   * runs once while the backend signature is validated and again for every
   * transaction in the consistency check, so a `mockImplementationOnce` lands
   * on whichever happens to be first and moves if that order ever changes.
   */
  async function withWalletReturning(
    changes: { group?: Uint8Array; fee?: number },
    run: () => Promise<unknown>,
  ) {
    const algosdk = require("algosdk");
    const original = algosdk.decodeSignedTransaction.getMockImplementation();
    algosdk.decodeSignedTransaction.mockImplementation((b: Uint8Array) => {
      const isWalletBlob = b.length === SIG_A.length && b[3] === SIG_A[3];
      return {
        txn: {
          _raw: b.slice(0, 3),
          group: (isWalletBlob && changes.group) || new Uint8Array([99]),
          fee: (isWalletBlob && changes.fee) || 1000,
        },
        sig: b.slice(3),
      };
    });
    try {
      await run();
    } finally {
      algosdk.decodeSignedTransaction.mockImplementation(original);
    }
  }


  /**
   * Replace what the *wallet's* blob decodes to, leaving the backend's alone.
   *
   * `withWalletReturning` covers the field-level divergences; this covers the
   * shapes that are not a transaction at all - a decoder that throws, a result
   * with no body - which the consistency check has to survive rather than
   * propagate, because a wallet returning rubbish must be reported as rubbish
   * and not as a stack trace.
   */
  async function withWalletDecodingTo(
    decode: (blob: Uint8Array) => unknown,
    run: () => Promise<unknown>,
    encode?: (txn: unknown) => Uint8Array,
  ) {
    const algosdk = require("algosdk");
    const original = algosdk.decodeSignedTransaction.getMockImplementation();
    const originalEncode = algosdk.encodeUnsignedTransaction.getMockImplementation();
    algosdk.decodeSignedTransaction.mockImplementation((b: Uint8Array) => {
      const isWalletBlob = b.length === SIG_A.length && b[3] === SIG_A[3];
      if (isWalletBlob) return decode(b);
      return {
        txn: { _raw: b.slice(0, 3), group: new Uint8Array([99]), fee: 1000 },
        sig: b.slice(3),
      };
    });
    if (encode) algosdk.encodeUnsignedTransaction.mockImplementation(encode);
    try {
      await run();
    } finally {
      algosdk.decodeSignedTransaction.mockImplementation(original);
      algosdk.encodeUnsignedTransaction.mockImplementation(originalEncode);
    }
  }

  it("reports an undecodable transaction rather than throwing from the decoder", async () => {
    const { d } = deps();

    await withWalletDecodingTo(
      () => {
        throw new Error("not msgpack");
      },
      () =>
        expect(signAndSendPartial(partial(), d)).rejects.toThrow(
          "[0] came back undecodable",
        ),
    );
  });

  it("reports a result carrying no transaction body", async () => {
    // `decodeSignedTransaction` resolving to something without `txn` is not a
    // shape any wallet should produce, which is exactly why it must not reach
    // `txn.group` and read off undefined.
    const { d } = deps();

    await withWalletDecodingTo(
      () => ({ sig: new Uint8Array([1]) }),
      () =>
        expect(signAndSendPartial(partial(), d)).rejects.toThrow(
          "[0] came back without a transaction body",
        ),
    );
  });

  it("reports a transaction it cannot re-encode to compare", async () => {
    // The byte comparison is the catch-all for a field this does not name, so
    // its own failure has to be reported rather than swallowed - otherwise a
    // transaction that cannot be compared reads as one that matched.
    const { d } = deps();

    await withWalletDecodingTo(
      (b: Uint8Array) => ({
        txn: { _raw: b.slice(0, 3), group: new Uint8Array([99]), fee: 1000 },
        sig: b.slice(3),
      }),
      () =>
        expect(signAndSendPartial(partial(), d)).rejects.toThrow(
          "[0] could not be re-encoded to compare",
        ),
      // only for the wallet's transaction: the backend signature is validated
      // by re-encoding too, outside any try, so throwing for everything fails
      // there first and tests nothing here
      (txn: any) => {
        if (txn?._raw?.[0] === TXN_A[0]) throw new Error("cannot encode");
        return txn?._raw ?? new Uint8Array([0]);
      },
    );
  });

  it("catches a change in a field it does not name", async () => {
    // Group and fee are guesses about what a wallet might do. This is the
    // assertion that does not depend on having guessed right.
    const { d } = deps();

    await withWalletDecodingTo(
      (b: Uint8Array) => ({
        txn: {
          _raw: new Uint8Array([9, 9, 9]),
          group: new Uint8Array([99]),
          fee: 1000,
        },
        sig: b.slice(3),
      }),
      () =>
        expect(signAndSendPartial(partial(), d)).rejects.toThrow(
          "[0] changed in some other field",
        ),
    );
  });

  it("treats an absent group as a divergence, not as a match", async () => {
    // `sameBytes` defaults an absent side to empty, so a returned transaction
    // carrying no group at all must still be caught - it is the shape a
    // rebuilt-from-scratch transaction has before anyone re-groups it.
    const { d } = deps();

    await withWalletDecodingTo(
      (b: Uint8Array) => ({
        txn: { _raw: b.slice(0, 3), group: undefined, fee: 1000 },
        sig: b.slice(3),
      }),
      () =>
        expect(signAndSendPartial(partial(), d)).rejects.toThrow("[0] re-grouped"),
    );
  });

  it("treats an absent fee as zero when comparing", async () => {
    const { d } = deps();

    await withWalletDecodingTo(
      (b: Uint8Array) => ({
        txn: { _raw: b.slice(0, 3), group: new Uint8Array([99]), fee: undefined },
        sig: b.slice(3),
      }),
      () =>
        expect(signAndSendPartial(partial(), d)).rejects.toThrow(
          "fee 1000 -> undefined",
        ),
    );
  });

  it("names the transaction when the wallet re-groups it", async () => {
    // The failure a post-quantum swap actually produced. algod says
    // `inconsistent group values: A != B` and names neither the transaction
    // nor the field, which cost a debugging session on its own.
    const { d } = deps();

    await withWalletReturning({ group: new Uint8Array([77]) }, () =>
      expect(signAndSendPartial(partial(), d)).rejects.toThrow(
        "[0] re-grouped",
      ),
    );
  });

  it("names the fee when the wallet corrects it", async () => {
    // A Falcon signature costs three minimum fees, so a wallet raising an
    // underpaid one is behaving reasonably and invalidating the backend's
    // signature over the group at the same time.
    const { d } = deps();

    await withWalletReturning({ fee: 3000 }, () =>
      expect(signAndSendPartial(partial(), d)).rejects.toThrow(
        "[0] fee 1000 -> 3000",
      ),
    );
  });

  it("reports a fee change and a re-group together, not one of them", async () => {
    // The reason this reports every divergence rather than the first: a wallet
    // that raises a fee must re-group to keep the group hash valid, so
    // "re-grouped" is the symptom you see and the fee change is the cause you
    // need. Post-quantum makes that the likely case - a Falcon signature costs
    // three minimum fees where this group pays one.
    const { d } = deps();

    await withWalletReturning(
      { group: new Uint8Array([77]), fee: 3000 },
      () =>
        expect(signAndSendPartial(partial(), d)).rejects.toThrow(
          "[0] re-grouped, fee 1000 -> 3000",
        ),
    );
  });

  it("does not submit a group it could not verify", async () => {
    const { d } = deps();

    await withWalletReturning({ group: new Uint8Array([77]) }, async () => {
      await expect(signAndSendPartial(partial(), d)).rejects.toThrow();
      expect(d.submit).not.toHaveBeenCalled();
    });
  });

  it("rejects a missing or misplaced quote authorization before signing", async () => {
    const { d } = deps();
    await expect(
      signAndSendPartial(
        { ...partial(), quoteSignerIndex: 0 },
        d,
      ),
    ).rejects.toThrow("final transaction");
    await expect(
      signAndSendPartial(
        { ...partial(), signedTransactions: {} },
        d,
      ),
    ).rejects.toThrow("Backend quote signature is missing");
    expect(d.signTransactions).not.toHaveBeenCalled();
  });

  it("rejects an empty group", async () => {
    const { d } = deps();
    await expect(
      signAndSendPartial(
        { transactions: [], signedTransactions: {}, quoteSignerIndex: 0 },
        d,
      ),
    ).rejects.toThrow("Empty transaction group");
  });

  it("rejects an invalid backend signature index", async () => {
    const { d } = deps();
    await expect(
      signAndSendPartial(
        {
          ...partial(),
          signedTransactions: { "2": new Uint8Array([4, 5, 6, 20]) },
        },
        d,
      ),
    ).rejects.toThrow("invalid group index");
  });

  it("rejects an empty backend signature blob", async () => {
    const { d } = deps();
    await expect(
      signAndSendPartial(
        { ...partial(), signedTransactions: { "1": new Uint8Array() } },
        d,
      ),
    ).rejects.toThrow("Backend signature is empty");
  });

  it("rejects a backend signature for different transaction bytes", async () => {
    const { d } = deps();
    await expect(
      signAndSendPartial(
        {
          ...partial(),
          signedTransactions: { "1": new Uint8Array([9, 9, 9, 20]) },
        },
        d,
      ),
    ).rejects.toThrow("does not match the grouped transaction");
  });

  it("rejects a backend blob that has no transaction body", async () => {
    const decodeSignedTransaction = jest.requireMock("algosdk")
      .decodeSignedTransaction;
    decodeSignedTransaction.mockImplementationOnce(() => ({
      sig: new Uint8Array([20]),
    }));
    const { d } = deps();
    await expect(signAndSendPartial(partial(), d)).rejects.toThrow(
      "does not match the grouped transaction",
    );
  });

  it("rejects a backend blob without a signature", async () => {
    const { d } = deps();
    await expect(
      signAndSendPartial(
        { ...partial(), signedTransactions: { "1": new Uint8Array([4, 5, 6]) } },
        d,
      ),
    ).rejects.toThrow("not signed");
  });

  it("rejects an ungrouped backend group", async () => {
    const decodeUnsignedTransaction = jest.requireMock("algosdk")
      .decodeUnsignedTransaction;
    decodeUnsignedTransaction.mockImplementationOnce((b: Uint8Array) => ({
      _raw: b,
      group: undefined,
    }));
    const { d } = deps();
    await expect(signAndSendPartial(partial(), d)).rejects.toThrow(
      "Backend group is not grouped",
    );
  });

  it("rejects an incomplete wallet response", async () => {
    const { d } = deps({
      signTransactions: jest.fn(async () => [SIG_A]),
    });
    await expect(signAndSendPartial(partial(), d)).rejects.toThrow(
      "incomplete transaction group",
    );
    expect(d.submit).not.toHaveBeenCalled();
  });

  it("rejects when the wallet omits a required user signature", async () => {
    const { d } = deps({
      signTransactions: jest.fn(async () => [null, null]),
    });
    await expect(signAndSendPartial(partial(), d)).rejects.toThrow(
      "Wallet did not sign a required transaction",
    );
    expect(d.submit).not.toHaveBeenCalled();
  });

  /**
   * A three-transaction group: two the wallet signs, one the backend signed.
   *
   * The two-transaction group above cannot express "one transaction diverged
   * and another was rubbish", which is the case that decides whether the
   * rescue probe is safe to run.
   */
  function partialOfThree(): PartialSignedGroup {
    return {
      transactions: [TXN_A, TXN_B, TXN_C],
      signedTransactions: { "2": SIG_C },
      quoteSignerIndex: 2,
    };
  }

  /** Decode each blob by its trailing signature byte rather than by call order. */
  function withDecodingByBlob(
    perBlob: Record<number, (b: Uint8Array) => unknown>,
    run: () => Promise<unknown>,
  ) {
    const algosdk = require("algosdk");
    const original = algosdk.decodeSignedTransaction.getMockImplementation();
    algosdk.decodeSignedTransaction.mockImplementation((b: Uint8Array) => {
      const decode = perBlob[b[b.length - 1]];
      if (decode) return decode(b);
      return {
        txn: { _raw: b.slice(0, 3), group: new Uint8Array([99]), fee: 1000 },
        sig: b.slice(3),
      };
    });
    return run().finally(() =>
      algosdk.decodeSignedTransaction.mockImplementation(original),
    );
  }

  it("asks whether the group could still be rescued, and says so", async () => {
    // The report names what changed; on its own that has cost two sessions of
    // guessing at what to do about it. Both wallet transactions carry the same
    // new group, which is also the case where only the first one may be taken
    // as the group to aim at - the second must not overwrite it.
    const { d } = deps();
    const regrouped = (b: Uint8Array) => ({
      txn: { _raw: b.slice(0, 3), group: new Uint8Array([77]), fee: 1000 },
      sig: b.slice(3),
    });

    await withDecodingByBlob({ 10: regrouped, 20: regrouped }, () =>
      expect(signAndSendPartial(partialOfThree(), d)).rejects.toThrow(
        /\[0\] re-grouped; \[1\] re-grouped - signing the authorisation last would/,
      ),
    );
  });

  it("does not guess at a rescue when a transaction did not decode", async () => {
    // The probe recomputes a group id over every member. One missing body
    // means the answer would be computed over something that is not the group
    // the wallet returned, and a confident wrong verdict is worse than none.
    const { d } = deps();

    await withDecodingByBlob(
      {
        10: (b: Uint8Array) => ({
          txn: { _raw: b.slice(0, 3), group: new Uint8Array([77]), fee: 1000 },
          sig: b.slice(3),
        }),
        20: () => {
          throw new Error("not msgpack");
        },
      },
      async () => {
        const error = await signAndSendPartial(partialOfThree(), d).catch(
          (e: Error) => e,
        );
        expect(String(error)).toContain("[1] came back undecodable");
        expect(String(error)).not.toContain("signing the authorisation last");
      },
    );
  });
});

// ---------------------------------------------------------------------------
// rescueDiagnosis — can the backend still authorise what came back?
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// signAndSendPartial — signing the authorisation last
// ---------------------------------------------------------------------------

describe("signAndSendPartial — re-authorisation", () => {
  // A transaction here is [tag, tag, tag, groupByte], so a group id survives
  // the encode/decode round trip these doubles perform. The module-level
  // doubles drop it, which would make the step that aligns the built
  // authorisation's group with the wallet's invisible: omit that step and the
  // happy path below fails, which is the point of paying for the extra byte.
  const OLD = 99;
  const NEW = 77;
  const TX0 = new Uint8Array([1, 2, 3, OLD]);
  const TX1 = new Uint8Array([4, 5, 6, OLD]);
  /** The backend's authorisation: the unsigned bytes with a signature byte. */
  const BACKEND = new Uint8Array([...TX1, 20]);
  /** What the wallet hands back for index 0: re-grouped, and signed. */
  const WALLET = new Uint8Array([1, 2, 3, NEW, 10]);
  /** The replacement authorisation, signed over the wallet's group. */
  const FRESH = new Uint8Array([4, 5, 6, NEW, 40]);

  function withGroupAwareAlgosdk(run: () => Promise<unknown>) {
    const algosdk = require("algosdk");
    const saved = {
      decodeSigned: algosdk.decodeSignedTransaction.getMockImplementation(),
      decode: algosdk.decodeUnsignedTransaction.getMockImplementation(),
      encode: algosdk.encodeUnsignedTransaction.getMockImplementation(),
      assign: algosdk.assignGroupID.getMockImplementation(),
    };
    algosdk.decodeUnsignedTransaction.mockImplementation((b: Uint8Array) => ({
      _raw: b.slice(0, 3),
      group: new Uint8Array([b[3]]),
      fee: 1000,
    }));
    algosdk.encodeUnsignedTransaction.mockImplementation((t: any) =>
      new Uint8Array([...(t._raw ?? [0]), t.group?.[0] ?? 0]),
    );
    algosdk.decodeSignedTransaction.mockImplementation((b: Uint8Array) => ({
      txn: { _raw: b.slice(0, 3), group: new Uint8Array([b[3]]), fee: 1000 },
      sig: b.slice(4),
    }));
    // The wallet's group is what a recomputation arrives at, which is the case
    // the retry is for. `rescueDiagnosis`'s own suite covers the arithmetic.
    algosdk.assignGroupID.mockImplementation((txns: any[]) => {
      txns.forEach((t) => (t.group = new Uint8Array([NEW])));
      return txns;
    });
    return run().finally(() => {
      algosdk.decodeSignedTransaction.mockImplementation(saved.decodeSigned);
      algosdk.decodeUnsignedTransaction.mockImplementation(saved.decode);
      algosdk.encodeUnsignedTransaction.mockImplementation(saved.encode);
      algosdk.assignGroupID.mockImplementation(saved.assign);
    });
  }

  function rescuable(
    reauthorize?: PartialSignedGroup["reauthorize"],
  ): PartialSignedGroup {
    return {
      transactions: [TX0, TX1],
      signedTransactions: { "1": BACKEND },
      quoteSignerIndex: 1,
      reauthorize,
    };
  }

  function walletDeps(overrides: Partial<SignAndSendDeps> = {}) {
    const { d, calls } = deps({
      signTransactions: jest.fn(async (txns: Uint8Array[]) =>
        txns.map((_: unknown, i: number) => (i === 0 ? WALLET : null)),
      ),
      ...overrides,
    });
    return { d, calls };
  }

  it("re-authorises a re-grouped group and submits it", async () => {
    // The whole point. Pera rewrote and re-grouped what it signed, so the
    // backend's authorization is stale; asking it to sign the group that came
    // out is what turns a failed swap into a swap.
    const reauthorize = jest.fn(async () => FRESH);
    const { d, calls } = walletDeps();

    await withGroupAwareAlgosdk(async () => {
      const txid = await signAndSendPartial(rescuable(reauthorize), d);

      expect(txid).toBe("TXID123");
      // it sends the wallet's transactions without the authorization, and the
      // authorization separately - the shape the engine endpoint takes
      expect(reauthorize).toHaveBeenCalledWith([WALLET], BACKEND);
      expect(calls.submitted).toEqual([WALLET, FRESH]);
    });
  });

  it("says the page is older than the bundle when it cannot ask", async () => {
    // **The message this test exists for.** "Would rescue it" reads as a
    // proposal when the code to do it is right here, and the first time a
    // reader saw that it cost a deploy's worth of guessing at which half was
    // missing. The widget markup and this bundle are different repositories
    // and ship separately, so the page being behind is the whole answer.
    const { d } = walletDeps();

    await withGroupAwareAlgosdk(async () => {
      const error = await signAndSendPartial(rescuable(), d).catch(
        (e: Error) => e,
      );

      expect(String(error)).toContain("[0] re-grouped");
      expect(String(error)).toContain("would rescue it");
      expect(String(error)).toContain("offers no re-authorisation endpoint");
      expect(d.submit).not.toHaveBeenCalled();
    });
  });

  it("refuses a replacement signed over a different group", async () => {
    // The answer comes from the network and goes straight into a group about
    // to be submitted, so it is checked exactly as the wallet's answer is.
    const reauthorize = jest.fn(async () => new Uint8Array([4, 5, 6, 55, 40]));
    const { d } = walletDeps();

    await withGroupAwareAlgosdk(async () => {
      await expect(signAndSendPartial(rescuable(reauthorize), d)).rejects.toThrow(
        "re-authorized a different group",
      );
      expect(d.submit).not.toHaveBeenCalled();
    });
  });

  it("refuses a replacement that is not the authorization it built", async () => {
    // The authorization's fee is paid by the quote signer's own account and
    // its note carries the floor this trade was quoted at. A replacement
    // differing in either is one to refuse, not to submit.
    const reauthorize = jest.fn(async () => new Uint8Array([9, 9, 9, NEW, 40]));
    const { d } = walletDeps();

    await withGroupAwareAlgosdk(async () => {
      await expect(signAndSendPartial(rescuable(reauthorize), d)).rejects.toThrow(
        "differs from the one it built",
      );
    });
  });

  it("refuses an unsigned replacement", async () => {
    const reauthorize = jest.fn(async () => new Uint8Array([4, 5, 6, NEW]));
    const { d } = walletDeps();

    await withGroupAwareAlgosdk(async () => {
      await expect(signAndSendPartial(rescuable(reauthorize), d)).rejects.toThrow(
        "is not signed",
      );
    });
  });

  it("refuses an undecodable replacement", async () => {
    const reauthorize = jest.fn(async () => FRESH);
    const { d } = walletDeps();

    await withGroupAwareAlgosdk(async () => {
      const algosdk = require("algosdk");
      const decode = algosdk.decodeSignedTransaction.getMockImplementation();
      algosdk.decodeSignedTransaction.mockImplementation((b: Uint8Array) => {
        if (b.length === FRESH.length && b[4] === 40) throw new Error("not msgpack");
        return decode(b);
      });

      await expect(signAndSendPartial(rescuable(reauthorize), d)).rejects.toThrow(
        "is undecodable",
      );
    });
  });

  it.each([
    ["nothing", undefined],
    ["an empty blob", new Uint8Array()],
  ])("refuses when the backend returns %s", async (_label, answer) => {
    const reauthorize = jest.fn(async () => answer as any);
    const { d } = walletDeps();

    await withGroupAwareAlgosdk(async () => {
      await expect(signAndSendPartial(rescuable(reauthorize), d)).rejects.toThrow(
        "no replacement quote authorization",
      );
    });
  });

  it("does not ask when the wallet raised the authorization's fee too", async () => {
    // Then the backend would have to take a fee for its own transaction from
    // this request, and that transaction is paid for by the quote signer's
    // account. No wallet has been seen doing it; until one is, refusing beats
    // a way to drain that account a microALGO at a time.
    const reauthorize = jest.fn(async () => FRESH);
    const { d } = walletDeps();

    await withGroupAwareAlgosdk(async () => {
      const algosdk = require("algosdk");
      // the recomputation only agrees once the authorisation's fee has moved
      algosdk.assignGroupID.mockImplementation((txns: any[]) => {
        const raised = txns.some((t) => Number(t.fee) > 1000);
        txns.forEach((t) => (t.group = new Uint8Array([raised ? NEW : 1])));
        return txns;
      });

      await expect(signAndSendPartial(rescuable(reauthorize), d)).rejects.toThrow(
        "with the post-quantum premium added to its fee",
      );
      expect(reauthorize).not.toHaveBeenCalled();
    });
  });

  it("does not ask when nothing the backend could sign would fit", async () => {
    const reauthorize = jest.fn(async () => FRESH);
    const { d } = walletDeps();

    await withGroupAwareAlgosdk(async () => {
      const algosdk = require("algosdk");
      algosdk.assignGroupID.mockImplementation((txns: any[]) => {
        txns.forEach((t) => (t.group = new Uint8Array([1])));
        return txns;
      });

      await expect(signAndSendPartial(rescuable(reauthorize), d)).rejects.toThrow(
        "would not rescue it",
      );
      expect(reauthorize).not.toHaveBeenCalled();
    });
  });
});

describe("rescueDiagnosis", () => {
  /**
   * A group id that actually depends on the group's contents.
   *
   * The module-level `assignGroupID` double stamps a constant, which is enough
   * for tests that only need transactions to come out grouped and useless
   * here: every question this function answers is "which set of bodies did the
   * wallet hash?", and a constant answers all of them the same way.
   *
   * Two properties are modelled because the real algosdk has them, and both
   * have already been wrong in this file's history. A body's fee changes the
   * id - otherwise the premium attempt is indistinguishable from the first.
   * And an existing group changes it too, because `assignGroupID` hashes the
   * fields it is handed and does **not** blank a group first; verified against
   * algosdk 3.7.0. That is what makes "forgot to clear the group" a failing
   * test rather than an invisible one.
   */
  const idOf = (bodies: Array<{ tag: number; fee: number; group?: number }>) =>
    bodies.reduce((sum, b) => sum + b.tag + b.fee + 7 * (b.group ?? 0), 0) & 0xff;

  function withHashingAlgosdk(run: () => void) {
    const algosdk = require("algosdk");
    const saved = {
      encode: algosdk.encodeUnsignedTransaction.getMockImplementation(),
      decode: algosdk.decodeUnsignedTransaction.getMockImplementation(),
      assign: algosdk.assignGroupID.getMockImplementation(),
    };
    // Four bytes, so the round trip the probe performs through encode/decode
    // preserves everything the id is computed over.
    algosdk.encodeUnsignedTransaction.mockImplementation((t: any) => {
      if (t.unencodable) throw new Error("cannot encode");
      const fee = Number(t.fee ?? 0);
      return new Uint8Array([t.tag, fee & 0xff, (fee >> 8) & 0xff, t.group?.[0] ?? 0]);
    });
    algosdk.decodeUnsignedTransaction.mockImplementation((b: Uint8Array) => ({
      tag: b[0],
      fee: b[1] | (b[2] << 8),
      group: b[3] ? new Uint8Array([b[3]]) : undefined,
    }));
    algosdk.assignGroupID.mockImplementation((txns: any[]) => {
      const id = idOf(
        txns.map((t) => ({
          tag: t.tag,
          fee: Number(t.fee ?? 0),
          group: t.group?.[0],
        })),
      );
      txns.forEach((t) => (t.group = new Uint8Array([id])));
      return txns;
    });
    try {
      run();
    } finally {
      algosdk.encodeUnsignedTransaction.mockImplementation(saved.encode);
      algosdk.decodeUnsignedTransaction.mockImplementation(saved.decode);
      algosdk.assignGroupID.mockImplementation(saved.assign);
    }
  }

  /** Two transactions as the wallet returned them, plus the authorisation. */
  const bodies = (quoteFee = 1000) => [
    { tag: 1, fee: 3000, group: new Uint8Array([77]) },
    { tag: 2, fee: 3000, group: new Uint8Array([77]) },
    { tag: 3, fee: quoteFee, group: new Uint8Array([99]) },
  ];

  it("finds the authorisation as built when that is what the wallet hashed", () => {
    // The good case for signing last: the wallet raised the fees on what it
    // signed, left the backend's transaction alone, and hashed it unchanged -
    // so the backend has only to stamp the new group id and sign again.
    withHashingAlgosdk(() => {
      const target = new Uint8Array([
        idOf([
          { tag: 1, fee: 3000 },
          { tag: 2, fee: 3000 },
          { tag: 3, fee: 1000 },
        ]),
      ]);

      expect(rescueDiagnosis(bodies(), 2, target)).toBe(
        "signing the authorisation last would rescue it: the wallet's group " +
          "covers the authorisation exactly as the backend built it",
      );
    });
  });

  it("finds it carrying the premium when the wallet raised that fee too", () => {
    // The other good case, and the reason there are two attempts: the wallet
    // does not sign the authorisation but does hash it, and it may have added
    // the premium to it in passing. The backend can match that - it just has
    // to know to.
    withHashingAlgosdk(() => {
      const target = new Uint8Array([
        idOf([
          { tag: 1, fee: 3000 },
          { tag: 2, fee: 3000 },
          { tag: 3, fee: 3000 },
        ]),
      ]);

      expect(rescueDiagnosis(bodies(), 2, target)).toBe(
        "signing the authorisation last would rescue it: the wallet's group " +
          "covers the authorisation with the post-quantum premium added to its fee",
      );
    });
  });

  it("says so when neither candidate fits", () => {
    // Then the wallet changed something else as well, sign-last is not enough
    // on its own, and the next step is to find out what - rather than to build
    // a second round trip that would have failed anyway.
    withHashingAlgosdk(() => {
      expect(rescueDiagnosis(bodies(), 2, new Uint8Array([3]))).toContain(
        "would not rescue it",
      );
    });
  });

  it("reports no rescue rather than throwing when a body cannot be encoded", () => {
    // This runs while an error is already being assembled. A diagnostic that
    // throws replaces the report it was meant to enrich, and the failure the
    // user sees becomes one about the diagnostic.
    withHashingAlgosdk(() => {
      const broken: any[] = bodies();
      broken[1] = { ...broken[1], unencodable: true };

      expect(rescueDiagnosis(broken, 2, new Uint8Array([3]))).toContain(
        "would not rescue it",
      );
    });
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

  it("(e) no opt-in legs for an ALGO output even with a referrer", async () => {
    const { d } = deps({
      // Would report 'not opted in' for asset 0 (accountAssetInformation errors),
      // which previously injected a bogus escrow self-pay. Must not be consulted.
      isOptedIn: jest.fn(async () => false),
    });
    await signAndSend([TXN_A], d, {
      outputAssetId: 0, // ALGO
      userNeedsOptIn: false,
      referrer: "REFERRER_ADDR",
    });
    expect(getReferrerLogicSig).not.toHaveBeenCalled();
    expect(prepareReferrerOptIntoAsset).not.toHaveBeenCalled();
    expect(d.isOptedIn).not.toHaveBeenCalled();

    // The group handed to the wallet is just the swap txn (no injected legs).
    const allTxns: Uint8Array[] = (d.signTransactions as jest.Mock).mock.calls[0][0];
    const indexesToSign: number[] = (d.signTransactions as jest.Mock).mock.calls[0][1];
    expect(allTxns).toHaveLength(1);
    expect(indexesToSign).toEqual([0]);
  });

  it("(f) no user opt-in leg for an ALGO output", async () => {
    const { d } = deps();
    const { makeAssetTransferTxnWithSuggestedParamsFromObject } =
      jest.requireMock("algosdk");
    makeAssetTransferTxnWithSuggestedParamsFromObject.mockClear();
    await signAndSend([TXN_A], d, {
      outputAssetId: 0, // ALGO
      userNeedsOptIn: true, // defensive: even if set, ALGO can't be opted into
    });
    expect(
      makeAssetTransferTxnWithSuggestedParamsFromObject,
    ).not.toHaveBeenCalled();
    const allTxns: Uint8Array[] = (d.signTransactions as jest.Mock).mock.calls[0][0];
    expect(allTxns).toHaveLength(1);
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

describe("assetCreator", () => {
  /**
   * The second opinion behind the dust sweep's forfeit check (`S2`). Every one
   * of these is a "fails closed" case except the first: the caller refuses a
   * forfeit whose creator it cannot confirm, so anything short of a real
   * address must arrive as null rather than as a value that will not match.
   */
  it("returns the creator algod reports", async () => {
    const getAsset = jest.fn().mockResolvedValue({
      params: { creator: "CREATORADDRESS" },
    });
    await expect(assetCreator(31566704, { getAsset })).resolves.toBe(
      "CREATORADDRESS",
    );
    expect(getAsset).toHaveBeenCalledWith(31566704);
  });

  it("returns null when the request throws", async () => {
    const getAsset = jest.fn().mockRejectedValue(new Error("404 not found"));
    await expect(assetCreator(1, { getAsset })).resolves.toBeNull();
  });

  it("returns null when the response carries no params", async () => {
    await expect(
      assetCreator(1, { getAsset: jest.fn().mockResolvedValue({}) }),
    ).resolves.toBeNull();
  });

  it("returns null when the response is null", async () => {
    await expect(
      assetCreator(1, { getAsset: jest.fn().mockResolvedValue(null) }),
    ).resolves.toBeNull();
  });

  it("returns null for an empty creator", async () => {
    await expect(
      assetCreator(1, {
        getAsset: jest.fn().mockResolvedValue({ params: { creator: "" } }),
      }),
    ).resolves.toBeNull();
  });

  it("returns null for a creator that is not a string", async () => {
    // A decoded address object would be compared against raw bytes and never
    // match, which reads to the user as "the engine lied" rather than as "we
    // could not tell". The type guard keeps those two outcomes distinct.
    await expect(
      assetCreator(1, {
        getAsset: jest
          .fn()
          .mockResolvedValue({ params: { creator: { publicKey: [1, 2] } } }),
      }),
    ).resolves.toBeNull();
  });
});
