import { webcrypto } from "crypto";
import {
  encodeUnsignedTransaction,
  generateAccount,
  makePaymentTxnWithSuggestedParamsFromObject,
  type SuggestedParams,
} from "algosdk";

import {
  ANSWER_WAIT_MS,
  RESUMABLE,
  RESUME_FOR_MS,
  RESUME_KEY,
  USE_WALLET_KEY,
  WALLETCONNECT_KEY,
  acceptApproval,
  acceptSignature,
  collect,
  connectStep,
  decryptPayload,
  forgetStep,
  inApp,
  installLogoutForget,
  offerSignIn,
  resumeStep,
  say,
  signStep,
  storeConnection,
  takeStep,
  walletSession,
  watchStep,
  type ConnectStep,
  type OpenSocket,
  type Session,
  type SignStep,
} from "./walletResume";

const subtle = webcrypto.subtle as unknown as SubtleCrypto;
Object.defineProperty(globalThis, "crypto", { value: webcrypto, configurable: true });

const URL_ = "https://www.asastats.com/accounts/login/";
const NOW = 1_800_000_000_000;
const KEY = "11".repeat(32);
const BRIDGE = "https://wallet-connect-h.perawallet.app";
const reader = generateAccount();
const ADDRESS = reader.addr.toString();
const NOTE = "asastats-login:abc123";

const SESSION: Session = {
  connected: false,
  bridge: BRIDGE,
  key: KEY,
  clientId: "client-1",
  clientMeta: { name: "ASA Stats" },
  handshakeId: 42,
  handshakeTopic: "topic-1",
};

const CONNECT: ConnectStep = {
  kind: "connect",
  wallet: "pera",
  url: URL_,
  at: NOW,
  bridge: BRIDGE,
  key: KEY,
  clientId: "client-1",
  handshakeId: 42,
  handshakeTopic: "topic-1",
  clientMeta: { name: "ASA Stats" },
};

const SIGN: SignStep = {
  kind: "sign",
  wallet: "defly",
  url: URL_,
  at: NOW,
  bridge: BRIDGE,
  key: KEY,
  clientId: "client-1",
  address: ADDRESS,
  nonce: "abc123",
  note: NOTE,
  apiBase: "/api/v2/wallet/login",
  next: "",
  binding: "cd".repeat(32),
};

const PARAMS: SuggestedParams = {
  fee: BigInt(1000),
  minFee: BigInt(1000),
  flatFee: true,
  firstValid: BigInt(1),
  lastValid: BigInt(1000),
  genesisID: "mainnet-v1.0",
  genesisHash: new Uint8Array(32),
};

/** A signed proof as the wallet returns it, base64. */
function proof(
  overrides: { sender?: typeof reader; note?: string; amount?: number; close?: boolean; rekey?: boolean } = {}
): string {
  const account = overrides.sender ?? reader;
  const txn = makePaymentTxnWithSuggestedParamsFromObject({
    sender: account.addr,
    receiver: account.addr,
    amount: overrides.amount ?? 0,
    note: new Uint8Array(Buffer.from(overrides.note ?? NOTE)),
    suggestedParams: PARAMS,
    ...(overrides.close ? { closeRemainderTo: generateAccount().addr } : {}),
    ...(overrides.rekey ? { rekeyTo: generateAccount().addr } : {}),
  });
  return Buffer.from(txn.signTxn(account.sk)).toString("base64");
}

/** WalletConnect v1 encryption, as the wallet does it. */
async function encrypt(message: unknown, keyHex = KEY, tamper = false): Promise<string> {
  const key = Buffer.from(keyHex, "hex");
  const iv = webcrypto.getRandomValues(new Uint8Array(16));
  const aes = await subtle.importKey("raw", key, "AES-CBC", false, ["encrypt"]);
  const data = new Uint8Array(
    await subtle.encrypt({ name: "AES-CBC", iv }, aes, new TextEncoder().encode(JSON.stringify(message)))
  );
  const mac = await subtle.importKey("raw", key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const hmac = new Uint8Array(await subtle.sign("HMAC", mac, Buffer.concat([data, iv])));
  if (tamper) hmac[0] ^= 1;
  const hex = (bytes: Uint8Array) => Buffer.from(bytes).toString("hex");
  return JSON.stringify({ data: hex(data), hmac: hex(hmac), iv: hex(iv) });
}

class FakeSocket {
  sent: string[] = [];
  closed = false;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => Promise<void>) | null = null;
  onerror: (() => void) | null = null;
  constructor(public url: string) {}
  send(message: string) {
    this.sent.push(message);
  }
  close() {
    this.closed = true;
  }
  /** Deliver a bridge frame and let the async handler finish. */
  async deliver(topic: string, payload: string) {
    await this.onmessage!({ data: JSON.stringify({ topic, type: "pub", payload }) });
  }
}

function opener(): { open: OpenSocket; sockets: FakeSocket[] } {
  const sockets: FakeSocket[] = [];
  const open = ((url: string) => {
    const socket = new FakeSocket(url);
    sockets.push(socket);
    return socket;
  }) as unknown as OpenSocket;
  return { open, sockets };
}

/** Wait until the fake socket exists and has its handlers. */
const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

function saved(step: unknown) {
  localStorage.setItem(RESUME_KEY, typeof step === "string" ? step : JSON.stringify(step));
}

const blocked = {
  getItem: () => null,
  setItem: () => {
    throw new Error("blocked");
  },
  removeItem: () => {
    throw new Error("blocked");
  },
} as unknown as Storage;

beforeEach(() => {
  localStorage.clear();
  document.body.innerHTML = "";
  document.documentElement.classList.add("in-app");
});

afterEach(() => {
  jest.useRealTimers();
});

describe("inApp and walletSession", () => {
  it("reads the in-app class", () => {
    expect(inApp()).toBe(true);
    document.documentElement.classList.remove("in-app");
    expect(inApp()).toBe(false);
  });

  it("reads the connector's session", () => {
    expect(walletSession({ client: { connector: { session: { ...SESSION, connected: true } } } })).toEqual({
      ...SESSION,
      connected: true,
    });
    const { clientMeta: _, ...bare } = SESSION;
    expect(walletSession({ client: { connector: { session: bare } } })?.clientMeta).toBeNull();
  });

  it.each([
    ["no wallet", undefined],
    ["no client", {}],
    ["no session", { client: { connector: {} } }],
    ["no key", { client: { connector: { session: { ...SESSION, key: 1 } } } }],
    ["no topic", { client: { connector: { session: { ...SESSION, handshakeTopic: 1 } } } }],
  ])("returns null for %s", (_, wallet) => {
    expect(walletSession(wallet)).toBeNull();
  });
});

describe("watchStep", () => {
  const pera = (session: Partial<Session> = SESSION) => ({ id: "pera", client: { connector: { session } } });

  it("saves the step on the wc: hand-off and when hidden, and forgets it on stop", () => {
    const stop = watchStep(pera(), connectStep("pera", URL_, () => NOW));
    window.dispatchEvent(new Event("beforeunload"));
    expect(JSON.parse(localStorage.getItem(RESUME_KEY)!)).toEqual(CONNECT);

    localStorage.clear();
    Object.defineProperty(document, "visibilityState", { value: "visible", configurable: true });
    document.dispatchEvent(new Event("visibilitychange"));
    expect(localStorage.getItem(RESUME_KEY)).toBeNull();
    Object.defineProperty(document, "visibilityState", { value: "hidden", configurable: true });
    document.dispatchEvent(new Event("visibilitychange"));
    expect(localStorage.getItem(RESUME_KEY)).not.toBeNull();

    stop();
    expect(localStorage.getItem(RESUME_KEY)).toBeNull();
    window.dispatchEvent(new Event("beforeunload"));
    expect(localStorage.getItem(RESUME_KEY)).toBeNull();
  });

  it("saves nothing when the step does not apply", () => {
    watchStep(pera({ ...SESSION, connected: true }), connectStep("pera", URL_));
    window.dispatchEvent(new Event("beforeunload"));
    watchStep({ id: "pera" }, connectStep("pera", URL_));
    window.dispatchEvent(new Event("beforeunload"));
    expect(localStorage.getItem(RESUME_KEY)).toBeNull();
  });

  it("does nothing outside the app or for other wallets (R9)", () => {
    watchStep({ id: "lute" }, connectStep("lute", URL_))();
    document.documentElement.classList.remove("in-app");
    const stop = watchStep(pera(), connectStep("pera", URL_));
    window.dispatchEvent(new Event("beforeunload"));
    expect(localStorage.getItem(RESUME_KEY)).toBeNull();
    stop();
  });

  it("survives blocked storage", () => {
    const target = { ...window, localStorage: blocked, document, addEventListener: window.addEventListener.bind(window), removeEventListener: window.removeEventListener.bind(window) } as unknown as Window;
    const stop = watchStep(pera(), connectStep("pera", URL_), target);
    expect(() => window.dispatchEvent(new Event("beforeunload"))).not.toThrow();
    expect(() => stop()).not.toThrow();
  });
});

describe("steps", () => {
  it("builds a sign step only for a connected session", () => {
    const fields = { wallet: "defly", url: URL_, address: ADDRESS, nonce: "abc123", note: NOTE, apiBase: SIGN.apiBase, next: "", binding: SIGN.binding };
    expect(signStep(fields, () => NOW)({ ...SESSION, connected: true })).toEqual(SIGN);
    expect(signStep(fields)(SESSION)).toBeNull();
    expect(connectStep("pera", URL_)(SESSION)?.at).toEqual(expect.any(Number));
    expect(signStep(fields)({ ...SESSION, connected: true })?.at).toEqual(expect.any(Number));
  });
});

describe("takeStep", () => {
  const take = () => takeStep(localStorage, URL_, NOW);

  it.each([
    ["a connect", CONNECT],
    ["a sign", SIGN],
  ])("returns %s once", (_, step) => {
    saved(step);
    expect(take()).toEqual(step);
    expect(localStorage.getItem(RESUME_KEY)).toBeNull();
  });

  it("leaves another page's fresh step", () => {
    saved({ ...CONNECT, url: "https://www.asastats.com/" });
    expect(take()).toBeNull();
    expect(localStorage.getItem(RESUME_KEY)).not.toBeNull();
  });

  it.each([
    ["expired", { ...CONNECT, at: NOW - RESUME_FOR_MS - 1 }],
    ["from the future", { ...CONNECT, at: NOW + 1 }],
    ["no time", { ...CONNECT, at: undefined }],
    ["an unknown wallet", { ...CONNECT, wallet: "lute" }],
    ["a foreign bridge (R6)", { ...CONNECT, bridge: "https://evil.example" }],
    ["the old public bridge", { ...CONNECT, bridge: "https://bridge.walletconnect.org" }],
    ["a bad key", { ...CONNECT, key: "zz" }],
    ["no client id", { ...CONNECT, clientId: "" }],
    ["a connect without handshake", { ...CONNECT, handshakeId: "1" }],
    ["a sign with a missing field", { ...SIGN, next: undefined }],
    ["a sign with a bad address", { ...SIGN, address: "NOPE" }],
    ["a sign posting elsewhere", { ...SIGN, apiBase: "https://evil.example/api" }],
    ["a sign without its binding", { ...SIGN, binding: undefined }],
    ["a sign with a bad binding", { ...SIGN, binding: "xy" }],
    ["an unknown kind", { ...CONNECT, kind: "other" }],
  ])("drops %s", (_, step) => {
    saved(step);
    expect(take()).toBeNull();
    expect(localStorage.getItem(RESUME_KEY)).toBeNull();
  });

  it("drops what is not JSON and ignores what is not a step", () => {
    saved("{");
    expect(take()).toBeNull();
    expect(localStorage.getItem(RESUME_KEY)).toBeNull();
    saved("5");
    expect(take()).toBeNull();
    expect(take()).toBeNull();
  });

  it("forgets without throwing on blocked storage", () => {
    expect(() => forgetStep(blocked)).not.toThrow();
    expect(() => forgetStep()).not.toThrow();
  });
});

describe("decryptPayload (R1)", () => {
  it("decrypts what verifies", async () => {
    expect(await decryptPayload(await encrypt({ id: 1 }), KEY, subtle)).toEqual({ id: 1 });
    expect(await decryptPayload(await encrypt({ id: 2 }), KEY)).toEqual({ id: 2 });
  });

  it.each([
    ["a tampered HMAC", async () => encrypt({ id: 1 }, KEY, true), KEY],
    ["another key", async () => encrypt({ id: 1 }, "22".repeat(32)), KEY],
    ["a short key", async () => encrypt({ id: 1 }), "11"],
    ["not hex", async () => JSON.stringify({ data: "zz", hmac: "00", iv: "00" }), KEY],
    ["odd hex", async () => JSON.stringify({ data: "0", hmac: "00", iv: "00" }), KEY],
    ["not JSON", async () => "{", KEY],
    ["a non-object message", async () => encrypt(5), KEY],
    ["a null message", async () => encrypt(null), KEY],
  ])("rejects %s", async (_, payload, key) => {
    expect(await decryptPayload(await payload(), key, subtle)).toBeNull();
  });
});

describe("collect (R8)", () => {
  it("subscribes to the client topic and takes the first accepted message", async () => {
    const { open, sockets } = opener();
    const result = collect(CONNECT, (m) => (m.id === 7 ? "yes" : null), open, 1000);
    await tick();
    const socket = sockets[0];
    expect(socket.url).toBe("wss://wallet-connect-h.perawallet.app");
    socket.onopen!();
    expect(JSON.parse(socket.sent[0])).toEqual({ topic: "client-1", type: "sub", payload: "", silent: true });

    await socket.onmessage!({ data: "not json" });
    await socket.deliver("other", await encrypt({ id: 7 }));
    await socket.onmessage!({ data: JSON.stringify({ topic: "client-1", payload: 5 }) });
    await socket.deliver("client-1", await encrypt({ id: 7 }, KEY, true));
    await socket.deliver("client-1", await encrypt({ id: 6 }));
    await socket.deliver("client-1", await encrypt({ id: 7 }));
    expect(await result).toBe("yes");
    expect(socket.closed).toBe(true);
    await socket.deliver("client-1", await encrypt({ id: 7 }));
  });

  it("stops on a refusal", async () => {
    const { open, sockets } = opener();
    const result = collect(CONNECT, () => false, open, 1000);
    await tick();
    await sockets[0].deliver("client-1", await encrypt({ id: 1 }));
    expect(await result).toBeNull();
  });

  it("gives up after the wait, on a socket error, or when it cannot open", async () => {
    jest.useFakeTimers();
    const { open, sockets } = opener();
    const late = collect(CONNECT, () => "x", open);
    jest.advanceTimersByTime(ANSWER_WAIT_MS);
    expect(await late).toBeNull();
    jest.useRealTimers();

    const failing = collect(CONNECT, () => "x", open, 1000);
    await tick();
    sockets[1].onerror!();
    expect(await failing).toBeNull();

    const throwing = (() => {
      throw new Error("no sockets");
    }) as unknown as OpenSocket;
    expect(await collect(CONNECT, () => "x", throwing, 1000)).toBeNull();
  });

  it("does not mind a socket that throws on close", async () => {
    const { open, sockets } = opener();
    const result = collect(CONNECT, () => false, open, 1000);
    await tick();
    sockets[0].close = () => {
      throw new Error("closed");
    };
    sockets[0].onerror!();
    expect(await result).toBeNull();
  });
});

describe("acceptApproval (R2)", () => {
  const accept = acceptApproval(CONNECT);

  it("takes this handshake's approval", () => {
    expect(
      accept({ id: 42, result: { approved: true, accounts: [ADDRESS], chainId: 416001, peerId: "p", peerMeta: { name: "Pera" } } })
    ).toEqual({ accounts: [ADDRESS], chainId: 416001, peerId: "p", peerMeta: { name: "Pera" } });
    expect(accept({ id: 42, result: { approved: true, accounts: [ADDRESS] } })).toEqual({
      accounts: [ADDRESS],
      chainId: 4160,
      peerId: "",
      peerMeta: null,
    });
  });

  it.each([
    ["another id", { id: 1, result: { approved: true, accounts: [ADDRESS] } }, null],
    ["a rejection", { id: 42, result: { approved: false } }, false],
    ["no result", { id: 42 }, false],
    ["no accounts", { id: 42, result: { approved: true, accounts: [] } }, false],
    ["accounts not a list", { id: 42, result: { approved: true, accounts: "x" } }, false],
    ["a bad account", { id: 42, result: { approved: true, accounts: ["NOPE"] } }, false],
  ])("returns the right answer for %s", (_, message, expected) => {
    expect(accept(message)).toBe(expected);
  });
});

describe("acceptSignature (R2)", () => {
  const accept = acceptSignature(SIGN);

  it("takes exactly our proof", () => {
    const signed = proof();
    expect(accept({ id: 1, result: [signed] })).toBe(signed);
    expect(accept({ id: 1, result: [null, signed] })).toBe(signed);
  });

  it("takes it as a list of byte values, as Defly sends it", () => {
    const signed = proof();
    const bytes = [...Buffer.from(signed, "base64")];
    expect(accept({ id: 1, result: [bytes] })).toBe(signed);
  });

  it.each([
    ["an empty byte list", []],
    ["values that are not bytes", [1, 256]],
    ["not a list or text", { 0: 1 }],
  ])("ignores %s", (_, item) => {
    expect(accept({ id: 1, result: [item] })).toBeNull();
  });

  it.each([
    ["a refusal", () => ({ id: 1, error: { message: "no" } }), false],
    ["no list", () => ({ id: 1, result: "x" }), null],
    ["two signatures", () => ({ id: 1, result: [proof(), proof()] }), null],
    ["another note", () => ({ id: 1, result: [proof({ note: "other" })] }), null],
    ["another signer", () => ({ id: 1, result: [proof({ sender: generateAccount() })] }), null],
    ["an amount", () => ({ id: 1, result: [proof({ amount: 1 })] }), null],
    ["a close-out", () => ({ id: 1, result: [proof({ close: true })] }), null],
    ["a rekey", () => ({ id: 1, result: [proof({ rekey: true })] }), null],
    ["garbage", () => ({ id: 1, result: ["!!"] }), null],
  ])("refuses %s", (_, message, expected) => {
    expect(accept(message())).toBe(expected);
  });

  it("refuses a transaction that is not a payment", () => {
    const txn = makePaymentTxnWithSuggestedParamsFromObject({ sender: reader.addr, receiver: reader.addr, amount: 0, suggestedParams: PARAMS });
    const unsigned = Buffer.from(encodeUnsignedTransaction(txn)).toString("base64");
    expect(accept({ id: 1, result: [unsigned] })).toBeNull();
  });
});

describe("storeConnection", () => {
  const approval = { accounts: [ADDRESS], chainId: 4160, peerId: "p", peerMeta: { name: "Pera" } };

  it("writes the three records the libraries read back (R7 shapes)", () => {
    localStorage.setItem(
      USE_WALLET_KEY,
      JSON.stringify({ wallets: { lute: { accounts: [], activeAccount: null } }, activeWallet: "lute", activeNetwork: "mainnet", customNetworkConfigs: {} })
    );
    storeConnection(CONNECT, approval, localStorage);
    expect(JSON.parse(localStorage.getItem(WALLETCONNECT_KEY)!)).toEqual({
      connected: true,
      accounts: [ADDRESS],
      chainId: 4160,
      bridge: BRIDGE,
      key: KEY,
      clientId: "client-1",
      clientMeta: { name: "ASA Stats" },
      peerId: "p",
      peerMeta: { name: "Pera" },
      handshakeId: 42,
      handshakeTopic: "topic-1",
    });
    expect(JSON.parse(localStorage.getItem("PeraWallet.Wallet")!)).toEqual({
      type: "pera-wallet",
      accounts: [ADDRESS],
      selectedAccount: ADDRESS,
    });
    const account = { name: "Pera Account 1", address: ADDRESS };
    expect(JSON.parse(localStorage.getItem(USE_WALLET_KEY)!)).toEqual({
      wallets: { lute: { accounts: [], activeAccount: null }, pera: { accounts: [account], activeAccount: account } },
      activeWallet: "pera",
      activeNetwork: "mainnet",
      customNetworkConfigs: {},
    });
  });

  it("starts use-wallet's state when there is none or it is broken", () => {
    storeConnection({ ...CONNECT, wallet: "defly" }, approval, localStorage);
    expect(JSON.parse(localStorage.getItem(USE_WALLET_KEY)!)).toMatchObject({ activeNetwork: "mainnet", activeWallet: "defly" });
    expect(JSON.parse(localStorage.getItem("DeflyWallet.Wallet")!).type).toBe("defly-wallet");
    localStorage.setItem(USE_WALLET_KEY, "{");
    storeConnection(CONNECT, approval, localStorage);
    expect(JSON.parse(localStorage.getItem(USE_WALLET_KEY)!).activeWallet).toBe("pera");
    localStorage.setItem(USE_WALLET_KEY, "null");
    storeConnection(CONNECT, approval, localStorage);
    expect(JSON.parse(localStorage.getItem(USE_WALLET_KEY)!).activeWallet).toBe("pera");
  });

  it("names the wallets as use-wallet does", () => {
    expect(RESUMABLE.pera.name).toBe("Pera");
    expect(RESUMABLE.defly.name).toBe("Defly");
  });
});

describe("resumeStep", () => {
  async function answered(step: unknown, message: unknown) {
    saved(step);
    const { open, sockets } = opener();
    const result = resumeStep(URL_, localStorage, open, NOW, 1000);
    await tick();
    if (message) await sockets[0].deliver("client-1", await encrypt(message));
    else sockets[0].onerror!();
    return result;
  }

  it("does nothing without a step", async () => {
    expect(await resumeStep(URL_, localStorage, opener().open, NOW)).toEqual({ kind: "none" });
  });

  it("stores an approved connect", async () => {
    const result = await answered(CONNECT, { id: 42, result: { approved: true, accounts: [ADDRESS] } });
    expect(result).toEqual({ kind: "connected", wallet: "pera" });
    expect(localStorage.getItem(WALLETCONNECT_KEY)).not.toBeNull();
  });

  it("reports a connect without an answer as lost", async () => {
    expect(await answered(CONNECT, null)).toEqual({ kind: "lost", wallet: "pera" });
  });

  it("reports a connect it cannot store as lost", async () => {
    saved(CONNECT);
    const { open, sockets } = opener();
    const storage = {
      getItem: (key: string) => localStorage.getItem(key),
      removeItem: (key: string) => localStorage.removeItem(key),
      setItem: () => {
        throw new Error("full");
      },
    } as unknown as Storage;
    const result = resumeStep(URL_, storage, open, NOW, 1000);
    await tick();
    await sockets[0].deliver("client-1", await encrypt({ id: 42, result: { approved: true, accounts: [ADDRESS] } }));
    expect(await result).toEqual({ kind: "lost", wallet: "pera" });
  });

  it("returns a collected signature, and nothing stored (R3)", async () => {
    const signed = proof();
    const result = await answered(SIGN, { id: 1, result: [signed] });
    expect(result).toEqual({ kind: "signed", step: SIGN, signed });
    expect(Object.values({ ...localStorage }).join()).not.toContain(signed);
  });

  it("reports a signature without an answer as lost", async () => {
    expect(await answered(SIGN, null)).toEqual({ kind: "lost", wallet: "defly" });
  });

  it("has working defaults", async () => {
    expect(await resumeStep(URL_)).toEqual({ kind: "none" });
  });

  it("opens a real WebSocket by default", async () => {
    jest.useFakeTimers({ now: NOW });
    saved(CONNECT);
    const sockets: FakeSocket[] = [];
    const real = globalThis.WebSocket;
    globalThis.WebSocket = jest.fn((url: string) => {
      const socket = new FakeSocket(url);
      sockets.push(socket);
      return socket;
    }) as unknown as typeof WebSocket;
    const result = resumeStep(URL_);
    await Promise.resolve();
    jest.advanceTimersByTime(ANSWER_WAIT_MS);
    expect(await result).toEqual({ kind: "lost", wallet: "pera" });
    expect(sockets[0].url).toBe("wss://wallet-connect-h.perawallet.app");
    globalThis.WebSocket = real;
  });
});

describe("say", () => {
  it("needs the card", () => {
    expect(say(document, "pera", "x")).toBeNull();
  });

  it("reuses the card's notice, or adds one, as text", () => {
    document.body.innerHTML = '<div id="wallet-pera"><div data-notice="info">old</div></div>';
    expect(say(document, "pera", "<b>new</b>")!.textContent).toBe("<b>new</b>");
    expect(document.querySelectorAll("[data-notice]")).toHaveLength(1);
    document.body.innerHTML = '<div id="wallet-pera"></div>';
    const notice = say(document, "pera", "fresh")!;
    expect(notice.getAttribute("role")).toBe("status");
    expect(notice.parentElement!.id).toBe("wallet-pera");
  });
});

describe("offerSignIn (R5)", () => {
  const card = () => (document.body.innerHTML = '<div id="wallet-defly"></div>');
  const buttons = () => [...document.querySelectorAll("button")] as HTMLButtonElement[];

  it("needs the card", () => {
    expect(offerSignIn(document, SIGN, "c2lnbmVk", "t")).toBeNull();
  });

  it("asks first and posts only on Finish", async () => {
    card();
    (global.fetch as jest.Mock).mockResolvedValue({ json: async () => ({ success: true, redirect_url: "/home/" }) });
    const go = jest.fn();
    const notice = offerSignIn(document, { ...SIGN, next: "/swap/" }, "c2lnbmVk", "token", go)!;
    expect(notice.textContent).toContain("Defly signed before your phone closed ASA Stats. Finish signing in?");
    expect(global.fetch).not.toHaveBeenCalled();

    buttons()[0].click();
    await tick();
    expect(global.fetch).toHaveBeenCalledWith("/api/v2/wallet/login/verify/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": "token" },
      body: JSON.stringify({ address: ADDRESS, signedTransaction: "c2lnbmVk", nonce: "abc123", chain: "algorand", binding: SIGN.binding, next: "/swap/" }),
    });
    expect(go).toHaveBeenCalledWith("/home/");
  });

  it("follows / without a redirect, and leaves next out when empty", async () => {
    card();
    (global.fetch as jest.Mock).mockResolvedValue({ json: async () => ({ success: true }) });
    const go = jest.fn();
    offerSignIn(document, SIGN, "c2lnbmVk", "t", go);
    buttons()[0].click();
    await tick();
    expect(JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body).next).toBeUndefined();
    expect(go).toHaveBeenCalledWith("/");
  });

  it.each([
    ["the server's error", async () => ({ json: async () => ({ success: false, error: "Nonce expired" }) }), "Nonce expired"],
    ["a refusal without a reason", async () => ({ json: async () => ({ success: false }) }), "Verification failed"],
  ])("shows %s", async (_, response, text) => {
    card();
    (global.fetch as jest.Mock).mockImplementation(response);
    offerSignIn(document, SIGN, "c2lnbmVk", "t", jest.fn());
    buttons()[0].click();
    await tick();
    expect(document.querySelector("[data-notice]")!.textContent).toBe(text);
  });

  it("shows a thrown non-error as text", async () => {
    card();
    (global.fetch as jest.Mock).mockRejectedValue("offline");
    offerSignIn(document, SIGN, "c2lnbmVk", "t", jest.fn());
    buttons()[0].click();
    await tick();
    expect(document.querySelector("[data-notice]")!.textContent).toBe("offline");
  });

  it("goes away on Not now", () => {
    card();
    offerSignIn(document, SIGN, "c2lnbmVk", "t");
    buttons()[1].click();
    expect(document.querySelector("[data-notice]")).toBeNull();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("follows the redirect with location.assign by default", async () => {
    card();
    (global.fetch as jest.Mock).mockResolvedValue({ json: async () => ({ success: true, redirect_url: "/home/" }) });
    const assign = jest.fn();
    (window.location as unknown as { assign: jest.Mock }).assign = assign;
    offerSignIn(document, SIGN, "c2lnbmVk", "t");
    buttons()[0].click();
    await tick();
    expect(assign).toHaveBeenCalledWith("/home/");
  });
});

describe("installLogoutForget (R4)", () => {
  it("drops the step on logout only", () => {
    installLogoutForget();
    document.body.innerHTML = '<form action="/accounts/login/"></form><form action="/accounts/logout/"></form>';
    const [login, logout] = [...document.forms];
    saved(CONNECT);
    login.dispatchEvent(new Event("submit", { bubbles: true }));
    expect(localStorage.getItem(RESUME_KEY)).not.toBeNull();
    logout.dispatchEvent(new Event("submit", { bubbles: true }));
    expect(localStorage.getItem(RESUME_KEY)).toBeNull();
    document.body.dispatchEvent(new Event("submit", { bubbles: true }));
  });

  it("uses this document by default", () => {
    expect(() => installLogoutForget(document)).not.toThrow();
  });
});
