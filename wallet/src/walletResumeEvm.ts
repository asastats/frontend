/**
 * @file Finish an EVM (WalletConnect v2) sign-in after the phone closed the app behind the wallet.
 *
 * Design and security rules V1-V7: capacitor/WALLET-RESUME-EVM-DESIGN.md and
 * WALLET-RESUME-EVM-SECURITY.md in the planning repo; docs/logbook.md here.
 */

import type { Eip1193Provider } from "./evmWalletComponent";
import { ANSWER_WAIT_MS, RESUME_FOR_MS, inApp } from "./walletResume";

/** localStorage key: the pending EVM step (`EvmStep`), one at a time. */
export const EVM_RESUME_KEY = "asastats.walletResumeEvm";

/** The only API bases a step may name (V6). */
export const EVM_API_BASES = ["/api/v2/wallet/login", "/api/v2/wallet/link"];

const ADDRESS = /^0x[0-9a-f]{40}$/;
const HEX64 = /^[0-9a-f]{64}$/;
const NONCE = /^[0-9a-f]{32}$/;
const PREFIX = /^[\w:-]{1,64}$/;

/** A connect the wallet was asked to approve. */
export interface EvmConnectStep {
  kind: "connect";
  url: string;
  at: number;
}

/** A login message the wallet was asked to sign. */
export interface EvmSignStep {
  kind: "sign";
  url: string;
  at: number;
  address: string;
  nonce: string;
  prefix: string;
  /** The page's login binding secret; the verify needs it. */
  binding: string;
  apiBase: string;
}

export type EvmStep = EvmConnectStep | EvmSignStep;

/** The WalletConnect history record fields read here (V7: a Jest test pins them). */
export interface WcHistoryRecord {
  id: number;
  topic: string;
  request: { method: string; params?: unknown };
  response?: { result?: unknown; error?: unknown };
}

/** The WalletConnect session fields read here. */
export interface WcSession {
  topic: string;
  expiry?: number;
  peer?: { metadata?: { name?: unknown } };
  namespaces?: Record<string, { accounts?: unknown; methods?: unknown }>;
}

/** The `@walletconnect/ethereum-provider` surface the resume uses. */
export interface RestoredProvider extends Eip1193Provider {
  session?: WcSession;
  signer: {
    session?: WcSession;
    createProviders?(): void;
    client: {
      session?: { getAll(): WcSession[] };
      core: {
        history: {
          values: WcHistoryRecord[];
          delete(topic: string, id?: number): void;
        };
      };
    };
    rpcProviders?: Record<
      string,
      { namespace?: { methods?: unknown }; updateNamespace?(ns: unknown): void } | undefined
    >;
  };
  disconnect(): Promise<void>;
}

/** What the restored page can do with the component that drew the buttons. */
export interface EvmResumeHost {
  /** Runs nonce, sign and verify with `provider`; resolves true once signed in. */
  signInWith(provider: Eip1193Provider, address: string, name: string): Promise<boolean>;
  /** Posts a collected signature to verify and follows the redirect; true on success. */
  verify(apiBase: string, nonce: string, signature: string, binding: string): Promise<boolean>;
}

/**
 * Note the EVM step being handed to the wallet (V1: app only, one at a time).
 *
 * @param step - the step.
 * @param target - the window.
 */
export function rememberEvmStep(step: EvmStep, target: Window = window): void {
  if (!inApp(target.document)) return;
  try {
    target.localStorage.setItem(EVM_RESUME_KEY, JSON.stringify(step));
  } catch {
    // storage blocked: the hand-off notice is all the reader gets
  }
}

/**
 * Drop the pending EVM step.
 *
 * @param storage - localStorage.
 */
export function forgetEvmStep(storage: Storage = localStorage): void {
  try {
    storage.removeItem(EVM_RESUME_KEY);
  } catch {
    // nothing to drop
  }
}

/**
 * Take this page's pending EVM step out of storage (before any network call).
 *
 * A fresh step for another page is left for that page until it expires.
 *
 * @param storage - localStorage.
 * @param href - this page.
 * @param now - the time, in ms.
 * @returns a well-formed step (V6), or null.
 */
export function takeEvmStep(storage: Storage, href: string, now: number): EvmStep | null {
  let step: (Partial<Omit<EvmSignStep, "kind">> & { kind?: unknown }) | null;
  try {
    step = JSON.parse(storage.getItem(EVM_RESUME_KEY) || "null");
  } catch {
    forgetEvmStep(storage);
    return null;
  }
  if (!step || typeof step !== "object") return null;
  const fresh = typeof step.at === "number" && step.at <= now && now - step.at <= RESUME_FOR_MS;
  if (fresh && typeof step.url === "string" && step.url !== href) return null;
  forgetEvmStep(storage);
  if (!fresh || typeof step.url !== "string") return null;
  if (step.kind === "connect") return { kind: "connect", url: step.url, at: step.at as number };
  if (step.kind !== "sign") return null;
  const { address, nonce, prefix, binding, apiBase } = step;
  if (typeof address !== "string" || !ADDRESS.test(address)) return null;
  if (typeof nonce !== "string" || !NONCE.test(nonce)) return null;
  if (typeof prefix !== "string" || !PREFIX.test(prefix)) return null;
  if (typeof binding !== "string" || !HEX64.test(binding)) return null;
  if (typeof apiBase !== "string" || !EVM_API_BASES.includes(apiBase)) return null;
  return { kind: "sign", url: step.url, at: step.at as number, address, nonce, prefix, binding, apiBase };
}

/**
 * The one EVM address of a session (V2), lower-cased.
 *
 * @param session - the restored session.
 * @returns the address, or null unless there is exactly one valid one.
 */
export function sessionAddress(session: WcSession | undefined): string | null {
  const accounts = session?.namespaces?.eip155?.accounts;
  if (!Array.isArray(accounts)) return null;
  const addresses = new Set(
    accounts.map((account) => String(account).split(":").pop()!.toLowerCase())
  );
  if (addresses.size !== 1) return null;
  const [address] = addresses;
  return ADDRESS.test(address) ? address : null;
}

/**
 * The wallet's name from the session's peer metadata, for text only.
 *
 * @param session - the restored session.
 * @returns the name, or "Your wallet".
 */
export function peerName(session: WcSession | undefined): string {
  const name = session?.peer?.metadata?.name;
  return typeof name === "string" && name.trim() ? name.trim().slice(0, 40) : "Your wallet";
}

/**
 * The newest session the sign client holds, made the provider's own.
 *
 * The provider takes the client's first session once, at init, so a connect the
 * wallet approves while the page restores, or after an older session, is not
 * its own yet (docs/logbook.md).
 *
 * @param provider - the restored provider.
 * @returns the session, or undefined.
 */
export function adoptSession(provider: RestoredProvider): WcSession | undefined {
  const sessions = provider.signer.client.session?.getAll() ?? [];
  if (!sessions.length) return provider.session;
  const newest = sessions.reduce((a, b) => ((b.expiry ?? 0) > (a.expiry ?? 0) ? b : a));
  if (provider.session?.topic === newest.topic) return provider.session;
  provider.signer.session = newest;
  provider.signer.createProviders?.();
  return provider.session ?? newest;
}

/**
 * Give a restored provider its session's methods back.
 *
 * Its rpc provider is rebuilt without them and then refuses `personal_sign`
 * (docs/logbook.md).
 *
 * @param provider - the restored provider.
 */
export function fixNamespace(provider: RestoredProvider): void {
  const rpc = provider.signer.rpcProviders?.eip155;
  const methods = provider.session?.namespaces?.eip155;
  if (rpc && methods && !Array.isArray(rpc.namespace?.methods)) rpc.updateNamespace?.(methods);
}

/**
 * The hex of a UTF-8 message, as `personal_sign` carries it.
 *
 * @param message - the message.
 * @returns `0x` and lower-case hex.
 */
export function messageHex(message: string): string {
  return (
    "0x" +
    Array.from(new TextEncoder().encode(message), (byte) => byte.toString(16).padStart(2, "0")).join("")
  );
}

/**
 * The wallet's answer to our sign request, if the library has stored it (V2).
 *
 * @param provider - the restored provider.
 * @param step - the sign step.
 * @returns the signature and its record, or null.
 */
export function signedAnswer(
  provider: RestoredProvider,
  step: EvmSignStep
): { signature: string; record: WcHistoryRecord } | null {
  const topic = provider.session?.topic;
  if (!topic) return null;
  const hex = messageHex(step.prefix + step.nonce);
  for (const record of provider.signer.client.core.history.values) {
    if (record.topic !== topic || record.request?.method !== "wc_sessionRequest") continue;
    const inner = (record.request.params as { request?: { method?: unknown; params?: unknown } })
      ?.request;
    if (inner?.method !== "personal_sign" || !Array.isArray(inner.params)) continue;
    const [message, address] = inner.params;
    if (String(message).toLowerCase() !== hex || String(address).toLowerCase() !== step.address) continue;
    const response = record.response;
    if (!response || response.error !== undefined) continue;
    if (typeof response.result !== "string" || !/^0x[0-9a-fA-F]{130}$/.test(response.result)) continue;
    return { signature: response.result, record };
  }
  return null;
}

/**
 * Delete the stored `personal_sign` answers of the provider's session (V3, E4).
 *
 * @param provider - any EIP-1193 provider; only WalletConnect's has a history.
 */
export function forgetSignatures(provider: unknown): void {
  try {
    const restored = provider as RestoredProvider;
    const topic = restored.session?.topic;
    const history = restored.signer?.client?.core?.history;
    if (!topic || !history) return;
    for (const record of [...history.values]) {
      const inner = (record.request?.params as { request?: { method?: unknown } })?.request;
      if (record.topic === topic && inner?.method === "personal_sign") history.delete(topic, record.id);
    }
  } catch {
    // not WalletConnect, or its internals moved: nothing kept to delete
  }
}

/**
 * Resolve with `check()`'s first truthy value, polling until `wait` ms pass.
 *
 * @param check - what to look for.
 * @param wait - how long, in ms.
 * @param every - poll interval, in ms.
 * @returns the value, or null.
 */
export async function waitFor<T>(
  check: () => T | null,
  wait: number = ANSWER_WAIT_MS,
  every = 500
): Promise<T | null> {
  const end = Date.now() + wait;
  for (;;) {
    const value = check();
    if (value) return value;
    if (Date.now() >= end) return null;
    await new Promise((resolve) => setTimeout(resolve, every));
  }
}

/**
 * Bring the EVM container into view: open the login dialog on its tab when it is closed.
 *
 * @param container - `#evm-wallet-connect`.
 */
export function reveal(container: HTMLElement): void {
  const dialog = container.closest("dialog");
  if (!dialog || dialog.open || typeof dialog.showModal !== "function") return;
  dialog.showModal();
  const panel = container.closest<HTMLElement>(".modal-tab-panel");
  // authmodal.js switches tabs on this link's click
  if (panel?.id) container.ownerDocument.querySelector<HTMLElement>(`[href="#${panel.id}"]`)?.click();
}

/**
 * Put `text` in the EVM container's notice (the one `app/walletHandoff.ts` shows), or a new one.
 *
 * @param container - `#evm-wallet-connect`.
 * @param text - what to say.
 * @returns the notice.
 */
export function sayEvm(container: HTMLElement, text: string): HTMLElement {
  const doc = container.ownerDocument;
  // #evm-app-error is the no-wallet banner, not ours
  let notice = container.querySelector<HTMLElement>("[data-notice]:not(#evm-app-error)");
  if (!notice) {
    notice = doc.createElement("div");
    notice.dataset.notice = "info";
    notice.setAttribute("role", "status");
    container.appendChild(notice);
  }
  notice.replaceChildren(doc.createTextNode(text));
  return notice;
}

/**
 * Ask a question in the notice with a yes and a no button (V4).
 *
 * @param container - `#evm-wallet-connect`.
 * @param text - the question.
 * @param yes - the yes button's label.
 * @param onYes - runs once on yes.
 * @param onNo - runs once on no.
 * @param handsOff - whether yes opens the wallet (app/walletHandoff.ts notes it).
 * @returns the notice.
 */
export function ask(
  container: HTMLElement,
  text: string,
  yes: string,
  onYes: () => Promise<void>,
  onNo: () => Promise<void>,
  handsOff = false
): HTMLElement {
  const doc = container.ownerDocument;
  const notice = sayEvm(container, text);
  const finish = doc.createElement("button");
  finish.type = "button";
  // app/walletHandoff.ts HANDOFF_BUTTONS matches this attribute
  if (handsOff) finish.dataset.evmHandoff = "";
  finish.className = "btn btn-primary btn-sm mt-2 mr-2";
  finish.textContent = yes;
  const cancel = doc.createElement("button");
  cancel.type = "button";
  cancel.className = "btn btn-ghost btn-sm mt-2";
  cancel.textContent = "Not now";
  const buttons = doc.createElement("div");
  buttons.append(finish, cancel);
  notice.appendChild(buttons);
  const answer = (run: () => Promise<void>) => async () => {
    finish.disabled = cancel.disabled = true;
    buttons.remove();
    await run();
  };
  finish.addEventListener("click", answer(onYes), { once: true });
  cancel.addEventListener("click", answer(onNo), { once: true });
  return notice;
}

/** What {@link resumeEvm} ended with, for tests and the logbook. */
export type EvmResumed = "lost" | "offered-connect" | "offered-sign" | "offered-again";

/**
 * After a restart, finish the EVM step the phone interrupted, asking first.
 *
 * @param container - `#evm-wallet-connect`.
 * @param host - the component on this page.
 * @param step - the step taken from storage.
 * @param restore - inits WalletConnect without its modal.
 * @param wait - how long to wait for the session or the answer, in ms.
 * @returns what was offered.
 */
export async function resumeEvm(
  container: HTMLElement,
  host: EvmResumeHost,
  step: EvmStep,
  restore: () => Promise<RestoredProvider>,
  wait: number = ANSWER_WAIT_MS
): Promise<EvmResumed> {
  reveal(container);
  // app/walletHandoff.ts may have put its notice outside the closed login dialog
  container.ownerDocument.querySelectorAll('[data-wallet-handoff="evm"]').forEach((notice) => {
    if (!container.contains(notice)) notice.remove();
  });
  sayEvm(container, "Checking your wallet's answer…");
  let provider: RestoredProvider;
  try {
    provider = await restore();
  } catch {
    return lost(container);
  }
  const disconnect = async () => {
    try {
      await provider.disconnect();
    } catch {
      // already gone
    }
  };
  const address = await waitFor(() => sessionAddress(adoptSession(provider)), wait);
  if (!address) {
    if (provider.session) await disconnect();
    return lost(container);
  }
  fixNamespace(provider);
  const name = peerName(provider.session);

  if (step.kind === "connect") {
    ask(
      container,
      `${name} connected before your phone closed ASA Stats. Finish signing in?`,
      "Finish signing in",
      async () => {
        sayEvm(container, `Open ${name} and sign the message.`);
        if (await host.signInWith(provider, address, name)) return;
        sayEvm(container, "That did not finish. Please connect again.");
        // V5: a failed resumed connect leaves no session behind
        await disconnect();
      },
      async () => {
        container.querySelector("[data-notice]:not(#evm-app-error)")?.remove();
        await disconnect();
      },
      true
    );
    return "offered-connect";
  }

  const answer = address === step.address ? await waitFor(() => signedAnswer(provider, step), wait) : null;
  if (!answer) {
    ask(
      container,
      `${name} did not answer before your phone closed ASA Stats. Sign in again?`,
      `Sign in with ${name}`,
      async () => {
        sayEvm(container, `Open ${name} and sign the message.`);
        if (!(await host.signInWith(provider, address, name))) {
          sayEvm(container, "That did not finish. Please connect again.");
        }
      },
      async () => {
        container.querySelector("[data-notice]:not(#evm-app-error)")?.remove();
      },
      true
    );
    return "offered-again";
  }
  const { signature, record } = answer;
  ask(
    container,
    `${name} signed before your phone closed ASA Stats. Finish signing in?`,
    "Finish signing in",
    async () => {
      provider.signer.client.core.history.delete(record.topic, record.id);
      await host.verify(step.apiBase, step.nonce, signature, step.binding);
    },
    async () => {
      provider.signer.client.core.history.delete(record.topic, record.id);
      container.querySelector("[data-notice]:not(#evm-app-error)")?.remove();
    }
  );
  return "offered-sign";
}

/**
 * Say the step was lost.
 *
 * @param container - `#evm-wallet-connect`.
 * @returns `"lost"`.
 */
function lost(container: HTMLElement): "lost" {
  sayEvm(
    container,
    "Your wallet did not answer in time, so that step did not finish. Please connect again."
  );
  return "lost";
}
