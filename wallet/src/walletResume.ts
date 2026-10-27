/**
 * @file Finish a Pera/Defly step after the phone closed the app behind the wallet.
 *
 * Design and security rules R1-R9: capacitor/WALLET-RESUME-DESIGN.md and
 * WALLET-RESUME-SECURITY.md in the planning repo; docs/logbook.md here.
 */

import { decodeSignedTransaction, isValidAddress } from "algosdk";

/** localStorage key: the pending step (`Step`), one at a time. */
export const RESUME_KEY = "asastats.walletResume";

/** How long a pending step may be finished: the server's login NONCE_TTL. */
export const RESUME_FOR_MS = 5 * 60 * 1000;

/** How long to wait for the wallet's answer on the bridge (R8). */
export const ANSWER_WAIT_MS = 20_000;

/** The libraries' own storage keys, read back by their reconnect (R7 tests pin them). */
export const WALLETCONNECT_KEY = "walletconnect";
export const USE_WALLET_KEY = "@txnlab/use-wallet:v5";

/** The only bridges a step may name (R6). */
const BRIDGE = /^https:\/\/wallet-connect-[a-z]\.perawallet\.app$/;

/** Wallets this works for, with their connect library's record. */
export const RESUMABLE: Record<string, { name: string; storage: string; type: string }> = {
  pera: { name: "Pera", storage: "PeraWallet.Wallet", type: "pera-wallet" },
  defly: { name: "Defly", storage: "DeflyWallet.Wallet", type: "defly-wallet" },
};

/** The WalletConnect v1 session fields a step needs. */
export interface Session {
  connected: boolean;
  bridge: string;
  key: string;
  clientId: string;
  clientMeta: unknown;
  handshakeId: number;
  handshakeTopic: string;
}

interface StepBase {
  wallet: string;
  url: string;
  at: number;
  bridge: string;
  key: string;
  clientId: string;
}

/** A connect the wallet was asked to approve. */
export interface ConnectStep extends StepBase {
  kind: "connect";
  handshakeId: number;
  handshakeTopic: string;
  clientMeta: unknown;
}

/** A sign-in proof the wallet was asked to sign. */
export interface SignStep extends StepBase {
  kind: "sign";
  address: string;
  nonce: string;
  note: string;
  apiBase: string;
  next: string;
  /** The page's login binding secret; the verify needs it. */
  binding: string;
}

export type Step = ConnectStep | SignStep;

/** What a page load found. */
export type Resumed =
  | { kind: "none" }
  | { kind: "lost"; wallet: string }
  | { kind: "connected"; wallet: string }
  | { kind: "signed"; step: SignStep; signed: string };

/** Opens a WebSocket; replaced in tests. */
export type OpenSocket = (url: string) => WebSocket;

/**
 * Whether this page runs in the ASA Stats app (R9).
 *
 * @param doc - the page.
 * @returns whether `in-app` is set on the root element.
 */
export function inApp(doc: Document = document): boolean {
  return doc.documentElement.classList.contains("in-app");
}

/**
 * The WalletConnect session of a use-wallet Pera/Defly wallet, if it has one.
 *
 * @param wallet - a use-wallet wallet (its `client.connector.session`).
 * @returns the session's fields, or null.
 */
export function walletSession(wallet: unknown): Session | null {
  const session = (wallet as { client?: { connector?: { session?: Partial<Session> } } })
    ?.client?.connector?.session;
  if (!session) return null;
  const { bridge, key, clientId, handshakeTopic, handshakeId } = session;
  if (typeof bridge !== "string" || typeof key !== "string" || typeof clientId !== "string")
    return null;
  if (typeof handshakeTopic !== "string" || typeof handshakeId !== "number") return null;
  return {
    connected: session.connected === true,
    bridge,
    key,
    clientId,
    clientMeta: session.clientMeta ?? null,
    handshakeId,
    handshakeTopic,
  };
}

/**
 * Drop the pending step.
 *
 * @param storage - localStorage.
 */
export function forgetStep(storage: Storage = localStorage): void {
  try {
    storage.removeItem(RESUME_KEY);
  } catch {
    // nothing to drop
  }
}

/**
 * Keep `step` while the wallet is in front; drop it once the page's own flow ends.
 *
 * Saves on `beforeunload` (fired for the `wc:` hand-off) and when the page is
 * hidden, reading the session at that moment.
 *
 * @param wallet - the use-wallet wallet being used.
 * @param describe - builds the step from the current session, or null.
 * @param target - the window.
 * @returns a stop function: call it when the flow finished in this page.
 */
export function watchStep(
  wallet: { id: string },
  describe: (session: Session) => Step | null,
  target: Window = window
): () => void {
  if (!inApp(target.document) || !RESUMABLE[wallet.id]) return () => undefined;
  const save = () => {
    const session = walletSession(wallet);
    const step = session && describe(session);
    if (!step) return;
    try {
      target.localStorage.setItem(RESUME_KEY, JSON.stringify(step));
    } catch {
      // storage blocked: the notice is all the reader gets, as before
    }
  };
  const hidden = () => {
    if (target.document.visibilityState === "hidden") save();
  };
  target.addEventListener("beforeunload", save);
  target.document.addEventListener("visibilitychange", hidden);
  return () => {
    target.removeEventListener("beforeunload", save);
    target.document.removeEventListener("visibilitychange", hidden);
    forgetStep(target.localStorage);
  };
}

/**
 * The step for a connect in progress.
 *
 * @param wallet - wallet id.
 * @param url - this page.
 * @param now - the time, in ms.
 * @returns a function for {@link watchStep}.
 */
export function connectStep(wallet: string, url: string, now: () => number = Date.now) {
  return (session: Session): ConnectStep | null =>
    session.connected
      ? null
      : {
          kind: "connect",
          wallet,
          url,
          at: now(),
          bridge: session.bridge,
          key: session.key,
          clientId: session.clientId,
          handshakeId: session.handshakeId,
          handshakeTopic: session.handshakeTopic,
          clientMeta: session.clientMeta,
        };
}

/**
 * The step for a sign-in proof in progress.
 *
 * @param fields - what the verify call will need.
 * @param now - the time, in ms.
 * @returns a function for {@link watchStep}.
 */
export function signStep(
  fields: Pick<
    SignStep,
    "wallet" | "url" | "address" | "nonce" | "note" | "apiBase" | "next" | "binding"
  >,
  now: () => number = Date.now
) {
  return (session: Session): SignStep | null =>
    session.connected
      ? {
          kind: "sign",
          ...fields,
          at: now(),
          bridge: session.bridge,
          key: session.key,
          clientId: session.clientId,
        }
      : null;
}

/**
 * Take this page's pending step out of storage (R4: before any network call).
 *
 * A step for another page is left for that page until it expires.
 *
 * @param storage - localStorage.
 * @param href - this page.
 * @param now - the time, in ms.
 * @returns a well-formed, allowed step, or null.
 */
export function takeStep(storage: Storage, href: string, now: number): Step | null {
  let step: (Partial<Omit<ConnectStep, "kind"> & Omit<SignStep, "kind">> & { kind?: string }) | null;
  try {
    step = JSON.parse(storage.getItem(RESUME_KEY) || "null");
  } catch {
    forgetStep(storage);
    return null;
  }
  if (!step || typeof step !== "object") return null;
  const fresh = typeof step.at === "number" && step.at <= now && now - step.at <= RESUME_FOR_MS;
  if (fresh && step.url !== href) return null;
  forgetStep(storage);
  if (!fresh || typeof step.wallet !== "string" || !RESUMABLE[step.wallet]) return null;
  if (typeof step.bridge !== "string" || !BRIDGE.test(step.bridge)) return null;
  if (typeof step.key !== "string" || !/^[0-9a-f]{64}$/.test(step.key)) return null;
  if (typeof step.clientId !== "string" || !step.clientId) return null;
  if (step.kind === "connect") {
    if (typeof step.handshakeId !== "number" || typeof step.handshakeTopic !== "string")
      return null;
    return step as ConnectStep;
  }
  if (step.kind === "sign") {
    const strings = [step.address, step.nonce, step.note, step.apiBase, step.next];
    if (strings.some((value) => typeof value !== "string")) return null;
    if (typeof step.binding !== "string" || !/^[0-9a-f]{64}$/.test(step.binding)) return null;
    if (!isValidAddress(step.address as string) || !step.apiBase?.startsWith("/")) return null;
    return step as SignStep;
  }
  return null;
}

/** Hex string to bytes; null when it is not hex. */
function hexBytes(hex: unknown): Uint8Array<ArrayBuffer> | null {
  if (typeof hex !== "string" || hex.length % 2 || !/^[0-9a-f]*$/i.test(hex)) return null;
  const bytes = new Uint8Array(new ArrayBuffer(hex.length / 2));
  for (let i = 0; i < bytes.length; i++) bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  return bytes;
}

/**
 * Decrypt a WalletConnect v1 payload, checking its HMAC first (R1).
 *
 * @param payload - the bridge message's `payload`: JSON `{data, hmac, iv}` in hex.
 * @param keyHex - the session key.
 * @param subtle - WebCrypto.
 * @returns the JSON-RPC message, or null for anything that does not verify.
 */
export async function decryptPayload(
  payload: string,
  keyHex: string,
  subtle: SubtleCrypto = crypto.subtle
): Promise<Record<string, unknown> | null> {
  try {
    const { data, hmac, iv } = JSON.parse(payload);
    const [cipher, mac, vector, key] = [data, hmac, iv, keyHex].map(hexBytes);
    if (!cipher || !mac || !vector || !key || key.length !== 32) return null;
    const signed = new Uint8Array(new ArrayBuffer(cipher.length + vector.length));
    signed.set(cipher);
    signed.set(vector, cipher.length);
    const macKey = await subtle.importKey("raw", key, { name: "HMAC", hash: "SHA-256" }, false, [
      "verify",
    ]);
    if (!(await subtle.verify("HMAC", macKey, mac, signed))) return null;
    const aesKey = await subtle.importKey("raw", key, "AES-CBC", false, ["decrypt"]);
    const plain = await subtle.decrypt({ name: "AES-CBC", iv: vector }, aesKey, cipher);
    const message = JSON.parse(new TextDecoder().decode(plain));
    return message && typeof message === "object" ? message : null;
  } catch {
    return null;
  }
}

/**
 * Wait on the bridge for the first message `accept` takes (R8: once, then close).
 *
 * @param step - the pending step.
 * @param accept - returns a value for the wanted message, `false` for a
 *   refusal (stop), or null to keep waiting.
 * @param open - opens the socket.
 * @param wait - how long, in ms.
 * @returns the accepted value, or null.
 */
export function collect<T>(
  step: Step,
  accept: (message: Record<string, unknown>) => T | false | null,
  open: OpenSocket,
  wait: number = ANSWER_WAIT_MS
): Promise<T | null> {
  return new Promise((resolve) => {
    let socket: WebSocket;
    let done = false;
    const finish = (value: T | null) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      try {
        socket.close();
      } catch {
        // already closed
      }
      resolve(value);
    };
    const timer = setTimeout(() => finish(null), wait);
    try {
      socket = open(step.bridge.replace(/^https:/, "wss:"));
    } catch {
      finish(null);
      return;
    }
    socket.onopen = () =>
      socket.send(JSON.stringify({ topic: step.clientId, type: "sub", payload: "", silent: true }));
    socket.onerror = () => finish(null);
    socket.onmessage = async (event: MessageEvent) => {
      let frame: { topic?: unknown; payload?: unknown };
      try {
        frame = JSON.parse(String(event.data));
      } catch {
        return;
      }
      if (frame.topic !== step.clientId || typeof frame.payload !== "string") return;
      const message = await decryptPayload(frame.payload, step.key);
      if (!message) return;
      const value = accept(message);
      if (value === false) finish(null);
      else if (value !== null) finish(value);
    };
  });
}

/**
 * Accept only the approval of this connect (R2).
 *
 * @param step - the connect.
 * @returns the accounts and the wallet's session fields, `false`, or null.
 */
export function acceptApproval(step: ConnectStep) {
  return (message: Record<string, unknown>) => {
    if (message.id !== step.handshakeId) return null;
    const result = message.result as Record<string, unknown> | undefined;
    if (!result || result.approved !== true) return false;
    const accounts = result.accounts;
    if (!Array.isArray(accounts) || !accounts.length) return false;
    if (!accounts.every((a) => typeof a === "string" && isValidAddress(a))) return false;
    return {
      accounts: accounts as string[],
      chainId: typeof result.chainId === "number" ? result.chainId : 4160,
      peerId: typeof result.peerId === "string" ? result.peerId : "",
      peerMeta: result.peerMeta ?? null,
    };
  };
}

/**
 * The bytes of one signed transaction in a wallet's answer: base64 text, or
 * (Defly, and Pera Connect allows it) a list of byte values.
 *
 * @param item - one entry of the JSON-RPC result.
 * @returns the bytes, or null.
 */
function signedBytes(item: unknown): Uint8Array | null {
  if (typeof item === "string") {
    try {
      return Uint8Array.from(atob(item), (c) => c.charCodeAt(0));
    } catch {
      return null;
    }
  }
  if (Array.isArray(item) && item.length && item.every((b) => Number.isInteger(b) && b >= 0 && b <= 255)) {
    return Uint8Array.from(item);
  }
  return null;
}

/**
 * Accept only a signature of this sign-in proof (R2): one signed 0-ALGO
 * self-payment from the step's address with exactly the step's note.
 *
 * @param step - the sign step.
 * @returns the signed transaction in base64, `false`, or null.
 */
export function acceptSignature(step: SignStep) {
  return (message: Record<string, unknown>) => {
    if ("error" in message) return false;
    const result = message.result;
    if (!Array.isArray(result)) return null;
    const signed = result.map(signedBytes).filter((bytes): bytes is Uint8Array => bytes !== null);
    if (signed.length !== 1) return null;
    try {
      const { txn } = decodeSignedTransaction(signed[0]);
      const sender = txn.sender.toString();
      const note = new TextDecoder().decode(txn.note);
      const pay = txn.payment;
      const ok =
        txn.type === "pay" &&
        sender === step.address &&
        note === step.note &&
        !!pay &&
        pay.amount === BigInt(0) &&
        pay.receiver.toString() === sender &&
        !pay.closeRemainderTo &&
        !txn.rekeyTo;
      return ok ? btoa(String.fromCharCode(...signed[0])) : null;
    } catch {
      return null;
    }
  };
}

/**
 * Store a connect the wallet approved where its library and use-wallet read it back.
 *
 * @param step - the connect.
 * @param approval - from {@link acceptApproval}.
 * @param storage - localStorage.
 */
export function storeConnection(
  step: ConnectStep,
  approval: { accounts: string[]; chainId: number; peerId: string; peerMeta: unknown },
  storage: Storage
): void {
  const { accounts } = approval;
  const wallet = RESUMABLE[step.wallet];
  storage.setItem(
    WALLETCONNECT_KEY,
    JSON.stringify({
      connected: true,
      accounts,
      chainId: approval.chainId,
      bridge: step.bridge,
      key: step.key,
      clientId: step.clientId,
      clientMeta: step.clientMeta,
      peerId: approval.peerId,
      peerMeta: approval.peerMeta,
      handshakeId: step.handshakeId,
      handshakeTopic: step.handshakeTopic,
    })
  );
  storage.setItem(
    wallet.storage,
    JSON.stringify({ type: wallet.type, accounts, selectedAccount: accounts[0] })
  );
  let state: Record<string, unknown> = {};
  try {
    state = JSON.parse(storage.getItem(USE_WALLET_KEY) || "{}") || {};
  } catch {
    state = {};
  }
  const named = accounts.map((address, i) => ({ name: `${wallet.name} Account ${i + 1}`, address }));
  storage.setItem(
    USE_WALLET_KEY,
    JSON.stringify({
      activeNetwork: "mainnet",
      ...state,
      wallets: {
        ...((state.wallets as object) || {}),
        [step.wallet]: { accounts: named, activeAccount: named[0] },
      },
      activeWallet: step.wallet,
    })
  );
}

/**
 * On page load, finish this page's pending step if the wallet answered.
 *
 * @param href - this page.
 * @param storage - localStorage.
 * @param open - opens the bridge socket.
 * @param now - the time, in ms.
 * @param wait - how long to wait for the answer, in ms.
 * @returns what happened.
 */
export async function resumeStep(
  href: string,
  storage: Storage = localStorage,
  open: OpenSocket = (url) => new WebSocket(url),
  now: number = Date.now(),
  wait: number = ANSWER_WAIT_MS
): Promise<Resumed> {
  const step = takeStep(storage, href, now);
  if (!step) return { kind: "none" };
  if (step.kind === "connect") {
    const approval = await collect(step, acceptApproval(step), open, wait);
    if (!approval) return { kind: "lost", wallet: step.wallet };
    try {
      storeConnection(step, approval, storage);
    } catch {
      return { kind: "lost", wallet: step.wallet };
    }
    return { kind: "connected", wallet: step.wallet };
  }
  const signed = await collect(step, acceptSignature(step), open, wait);
  return signed ? { kind: "signed", step, signed } : { kind: "lost", wallet: step.wallet };
}

/**
 * Put `text` in the wallet card's notice (the one `app/walletHandoff.ts` shows), or a new one.
 *
 * @param doc - the page.
 * @param wallet - wallet id.
 * @param text - what to say.
 * @returns the notice, or null without the card.
 */
export function say(doc: Document, wallet: string, text: string): HTMLElement | null {
  const card = doc.getElementById(`wallet-${wallet}`);
  if (!card) return null;
  let notice = card.querySelector<HTMLElement>("[data-notice]");
  if (!notice) {
    notice = doc.createElement("div");
    notice.dataset.notice = "info";
    notice.setAttribute("role", "status");
    card.appendChild(notice);
  }
  notice.replaceChildren(doc.createTextNode(text));
  return notice;
}

/**
 * Ask before using a collected signature to sign in (R5), then post it.
 *
 * @param doc - the page.
 * @param step - the sign step.
 * @param signed - the signed proof, base64; never stored (R3).
 * @param csrf - the CSRF token.
 * @param go - follows the server's redirect.
 * @returns the notice holding the question, or null without the card.
 */
export function offerSignIn(
  doc: Document,
  step: SignStep,
  signed: string,
  csrf: string,
  go: (url: string) => void = (url) => window.location.assign(url)
): HTMLElement | null {
  const name = RESUMABLE[step.wallet].name;
  const notice = say(doc, step.wallet, `${name} signed before your phone closed ASA Stats. Finish signing in?`);
  if (!notice) return null;
  const finish = doc.createElement("button");
  finish.type = "button";
  finish.className = "btn btn-primary btn-sm mt-2 mr-2";
  finish.textContent = "Finish signing in";
  const cancel = doc.createElement("button");
  cancel.type = "button";
  cancel.className = "btn btn-ghost btn-sm mt-2";
  cancel.textContent = "Not now";
  const buttons = doc.createElement("div");
  buttons.append(finish, cancel);
  notice.appendChild(buttons);
  cancel.addEventListener("click", () => notice.remove());
  finish.addEventListener(
    "click",
    async () => {
      finish.disabled = cancel.disabled = true;
      try {
        const response = await fetch(`${step.apiBase}/verify/`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
          body: JSON.stringify({
            address: step.address,
            signedTransaction: signed,
            nonce: step.nonce,
            chain: "algorand",
            binding: step.binding,
            ...(step.next ? { next: step.next } : {}),
          }),
        });
        const data = await response.json();
        if (!data.success) throw new Error(data.error || "Verification failed");
        go(data.redirect_url || "/");
      } catch (error: unknown) {
        say(doc, step.wallet, error instanceof Error ? error.message : String(error));
      }
    },
    { once: true }
  );
  return notice;
}

/**
 * Drop a pending step when the reader logs out (R4).
 *
 * @param doc - the page.
 */
export function installLogoutForget(doc: Document = document): void {
  doc.addEventListener(
    "submit",
    (event) => {
      const form = event.target as HTMLFormElement | null;
      if (form?.action?.includes("/accounts/logout/")) forgetStep(doc.defaultView?.localStorage);
    },
    true
  );
}
