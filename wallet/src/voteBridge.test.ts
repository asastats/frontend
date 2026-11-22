import {
  ABIMethod,
  decodeAddress,
  decodeUnsignedTransaction,
  encodeUnsignedTransaction,
  type Transaction,
} from "algosdk";
import {
  buildVoteTransaction,
  castVote,
  voteBoxes,
  type VoteDeps,
  type VoteRequest,
} from "./voteBridge";

const SEAT = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M";
const PARAMS = {
  fee: 0n,
  minFee: 1000n,
  firstValid: 100n,
  lastValid: 1100n,
  genesisID: "testnet-v1.0",
  genesisHash: new Uint8Array(32).fill(7),
};

function request(overrides: Partial<VoteRequest> = {}): VoteRequest {
  return {
    seat: SEAT,
    appId: 775947805,
    permissionAppId: 750094865,
    sessionId: 2,
    option: 1,
    method: "vote(uint64,uint64)void",
    ...overrides,
  };
}

function deps(overrides: Partial<VoteDeps> = {}): VoteDeps {
  return {
    accounts: jest.fn(() => [SEAT]),
    useAccount: jest.fn(),
    signTransactions: jest.fn().mockResolvedValue([Uint8Array.of(9)]),
    suggestedParams: jest.fn().mockResolvedValue(PARAMS),
    submit: jest.fn().mockResolvedValue("TXID"),
    waitForConfirmation: jest.fn().mockResolvedValue(undefined),
    ...overrides,
  };
}

const sessionId = (n: number) => {
  const bytes = new Uint8Array(8);
  new DataView(bytes.buffer).setBigUint64(0, BigInt(n));
  return Array.from(bytes);
};

describe("voteBoxes", () => {
  it("names the session, ballot and permission boxes as dapp/helpers.py does", () => {
    const seatKey = Array.from(decodeAddress(SEAT).publicKey);
    const boxes = voteBoxes(request());
    expect(boxes.map((box) => box.appIndex)).toEqual([775947805, 775947805, 750094865]);
    expect(Array.from(boxes[0].name)).toEqual([0x73, ...sessionId(2)]);
    expect(Array.from(boxes[1].name)).toEqual([0x76, ...sessionId(2), ...seatKey]);
    expect(Array.from(boxes[2].name)).toEqual(seatKey);
  });
});

describe("buildVoteTransaction", () => {
  it("calls vote(session, option) with the inner call's fee and references", () => {
    const txn: Transaction = buildVoteTransaction(request(), PARAMS);
    const app = txn.applicationCall!;
    expect(txn.sender.toString()).toBe(SEAT);
    expect(txn.fee).toBe(2000n);
    expect(app.appIndex).toBe(775947805n);
    expect(app.foreignApps).toEqual([750094865n]);
    const method = ABIMethod.fromSignature("vote(uint64,uint64)void");
    expect(Array.from(app.appArgs[0])).toEqual(Array.from(method.getSelector()));
    expect(Array.from(app.appArgs[1])).toEqual(sessionId(2));
    expect(Array.from(app.appArgs[2])).toEqual(sessionId(1));
    const encoded = decodeUnsignedTransaction(encodeUnsignedTransaction(txn)).applicationCall!;
    expect(encoded.boxes.map((box) => box.appIndex)).toEqual([0n, 0n, 750094865n]);
  });

  it("takes the default minimum fee when the parameters carry none", () => {
    const { minFee, ...withoutMinFee } = PARAMS;
    expect(minFee).toBe(1000n);
    expect(buildVoteTransaction(request(), withoutMinFee).fee).toBe(2000n);
  });

  it("refuses a method that is not vote's shape", () => {
    expect(() => buildVoteTransaction(request({ method: "vote(uint64)void" }), PARAMS)).toThrow(
      "Unexpected vote method: vote(uint64)void",
    );
  });
});

describe("castVote", () => {
  it("selects the seat, signs, submits and waits", async () => {
    const d = deps();
    await expect(castVote(request(), d)).resolves.toBe("TXID");
    expect(d.useAccount).toHaveBeenCalledWith(SEAT);
    const [txns, indexes] = (d.signTransactions as jest.Mock).mock.calls[0];
    expect(indexes).toEqual([0]);
    expect(decodeUnsignedTransaction(txns[0]).sender.toString()).toBe(SEAT);
    expect(d.submit).toHaveBeenCalledWith([Uint8Array.of(9)]);
    expect(d.waitForConfirmation).toHaveBeenCalledWith("TXID");
  });

  it("asks for the seat's wallet when it is not connected", async () => {
    const d = deps({ accounts: () => ["OTHER"] });
    await expect(castVote(request(), d)).rejects.toThrow(`Connect the wallet holding ${SEAT} first`);
    expect(d.signTransactions).not.toHaveBeenCalled();
  });

  it("reports a wallet that declined to sign", async () => {
    const d = deps({ signTransactions: jest.fn().mockResolvedValue([null]) });
    await expect(castVote(request(), d)).rejects.toThrow("The wallet did not sign the vote");
    expect(d.submit).not.toHaveBeenCalled();
  });
});
