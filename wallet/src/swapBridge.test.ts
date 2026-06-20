import {
  optIn,
  signAndSend,
  type OptInDeps,
  type SignAndSendDeps,
} from "./swapBridge";

const TXN_A = new Uint8Array([1, 2, 3]);
const TXN_B = new Uint8Array([4, 5, 6]);
const SIG_A = new Uint8Array([10]);
const SIG_B = new Uint8Array([20]);

function deps(overrides: Partial<SignAndSendDeps> = {}): {
  d: SignAndSendDeps;
  calls: { signed?: Uint8Array[]; submitted?: Uint8Array[]; confirmed?: string };
} {
  const calls: any = {};
  const d: SignAndSendDeps = {
    activeAddress: jest.fn(() => "AAAA"),
    signTransactions: jest.fn(async (txns: Uint8Array[]) => {
      calls.signed = txns;
      return [SIG_A, SIG_B].slice(0, txns.length);
    }),
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

describe("signAndSend", () => {
  it("signs, submits and confirms in order and returns the txid", async () => {
    const { d, calls } = deps();
    const txid = await signAndSend([TXN_A, TXN_B], d);

    expect(calls.signed).toEqual([TXN_A, TXN_B]);
    expect(calls.submitted).toEqual([SIG_A, SIG_B]);
    expect(calls.confirmed).toBe("TXID123");
    expect(txid).toBe("TXID123");
  });

  it("throws on an empty group and signs nothing", async () => {
    const { d } = deps();
    await expect(signAndSend([], d)).rejects.toThrow("Empty transaction group");
    expect(d.signTransactions).not.toHaveBeenCalled();
    expect(d.submit).not.toHaveBeenCalled();
  });

  it("throws when no wallet account is active and signs nothing", async () => {
    const { d } = deps({ activeAddress: jest.fn(() => null) });
    await expect(signAndSend([TXN_A], d)).rejects.toThrow("No active wallet account");
    expect(d.signTransactions).not.toHaveBeenCalled();
    expect(d.submit).not.toHaveBeenCalled();
  });

  it("throws and does not submit when a transaction is left unsigned", async () => {
    const { d } = deps({
      signTransactions: jest.fn(async () => [SIG_A, null]),
    });
    await expect(signAndSend([TXN_A, TXN_B], d)).rejects.toThrow(
      "Wallet did not return a signature for every transaction"
    );
    expect(d.submit).not.toHaveBeenCalled();
    expect(d.waitForConfirmation).not.toHaveBeenCalled();
  });

  it("propagates a signer rejection (user cancel) and does not submit", async () => {
    const { d } = deps({
      signTransactions: jest.fn().mockRejectedValue(new Error("user rejected")),
    });
    await expect(signAndSend([TXN_A], d)).rejects.toThrow("user rejected");
    expect(d.submit).not.toHaveBeenCalled();
  });

  it("propagates a submit rejection and does not confirm", async () => {
    const { d } = deps({
      submit: jest.fn().mockRejectedValue(new Error("overspend")),
    });
    await expect(signAndSend([TXN_A], d)).rejects.toThrow("overspend");
    expect(d.waitForConfirmation).not.toHaveBeenCalled();
  });

  it("propagates a confirmation failure", async () => {
    const { d } = deps({
      waitForConfirmation: jest.fn().mockRejectedValue(new Error("rejected in block")),
    });
    await expect(signAndSend([TXN_A], d)).rejects.toThrow("rejected in block");
  });
});


const OPTIN_TXN = new Uint8Array([7, 7, 7]);

function optInDeps(
  overrides: Partial<OptInDeps> = {}
): { d: OptInDeps; calls: { built?: number; signed?: Uint8Array[] } } {
  const calls: any = {};
  const d: OptInDeps = {
    activeAddress: jest.fn(() => "AAAA"),
    buildOptIn: jest.fn(async (assetId: number) => {
      calls.built = assetId;
      return [OPTIN_TXN];
    }),
    signTransactions: jest.fn(async (txns: Uint8Array[]) => {
      calls.signed = txns;
      return [SIG_A];
    }),
    submit: jest.fn(async () => "OPTINTXID"),
    waitForConfirmation: jest.fn(async () => {}),
    ...overrides,
  };
  return { d, calls };
}

describe("optIn", () => {
  it("builds the opt-in txn then signs, submits and confirms it", async () => {
    const { d, calls } = optInDeps();
    const txid = await optIn(31566704, d);

    expect(calls.built).toBe(31566704);
    expect(calls.signed).toEqual([OPTIN_TXN]);
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
