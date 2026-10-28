/**
 * @jest-environment jsdom
 */

import {
  EVM_RESUME_KEY,
  ask,
  fixNamespace,
  forgetEvmStep,
  forgetSignatures,
  messageHex,
  peerName,
  rememberEvmStep,
  resumeEvm,
  reveal,
  sayEvm,
  sessionAddress,
  signedAnswer,
  adoptSession,
  takeEvmStep,
  waitFor,
  type EvmResumeHost,
  type EvmSignStep,
  type RestoredProvider,
  type WcHistoryRecord,
  type WcSession,
} from "./walletResumeEvm";

const PAGE = "https://www.asastats.com/accounts/login/";
const NOW = 1_800_000_000_000;
const ADDRESS = "0xf74bbabffd0e455934b2b450ea391d59410cf361";
const NONCE = "0123456789abcdef0123456789abcdef";
const BINDING = "ab".repeat(32);
const SIGNATURE = "0x" + "1b".repeat(65);
const TOPIC = "08b798c9";

const SIGN: EvmSignStep = {
  kind: "sign",
  url: PAGE,
  at: NOW - 1000,
  address: ADDRESS,
  nonce: NONCE,
  prefix: "asastats-auth:",
  binding: BINDING,
  apiBase: "/api/v2/wallet/login",
};

/** A blocked storage: every call throws. */
const blocked = {
  getItem: () => {
    throw new Error("blocked");
  },
  setItem: () => {
    throw new Error("blocked");
  },
  removeItem: () => {
    throw new Error("blocked");
  },
} as unknown as Storage;

function session(over: Partial<WcSession> = {}): WcSession {
  return {
    topic: TOPIC,
    peer: { metadata: { name: "Trust Wallet" } },
    namespaces: { eip155: { accounts: [`eip155:1:${ADDRESS}`], methods: ["personal_sign"] } },
    ...over,
  };
}

/** The history record WalletConnect 2.23.9 keeps for an answered personal_sign (V7). */
function signRecord(over: Partial<WcHistoryRecord> = {}): WcHistoryRecord {
  return {
    id: 1793188162983268,
    topic: TOPIC,
    request: {
      method: "wc_sessionRequest",
      params: {
        request: { method: "personal_sign", params: [messageHex(SIGN.prefix + SIGN.nonce), ADDRESS] },
        chainId: "eip155:1",
      },
    },
    response: { result: SIGNATURE },
    ...over,
  };
}

function provider(
  over: { session?: WcSession; records?: WcHistoryRecord[]; rpcMethods?: unknown; stored?: WcSession[] } = {}
): RestoredProvider & { updateNamespace: jest.Mock; deleteRecord: jest.Mock } {
  const records = over.records ?? [];
  const updateNamespace = jest.fn();
  const deleteRecord = jest.fn((topic: string, id?: number) => {
    const at = records.findIndex((r) => r.topic === topic && r.id === id);
    if (at >= 0) records.splice(at, 1);
  });
  const signer: RestoredProvider["signer"] = {
    session: "session" in over ? over.session : session(),
    createProviders: jest.fn(),
    client: {
      session: { getAll: () => over.stored ?? [] },
      core: { history: { values: records, delete: deleteRecord } },
    },
    rpcProviders: { eip155: { namespace: { methods: over.rpcMethods }, updateNamespace } },
  };
  return {
    // as @walletconnect/ethereum-provider: the session lives on the signer
    get session() {
      return signer.session;
    },
    request: jest.fn(),
    disconnect: jest.fn().mockResolvedValue(undefined),
    signer,
    updateNamespace,
    deleteRecord,
  };
}

function container(): HTMLElement {
  document.body.innerHTML = `
    <main></main>
    <div id="evm-wallet-connect">
      <div id="evm-app-error" data-notice="error" style="display:none"></div>
      <div id="evm-wallet-list"></div>
    </div>`;
  return document.getElementById("evm-wallet-connect")!;
}

function host(over: Partial<EvmResumeHost> = {}): EvmResumeHost & {
  signInWith: jest.Mock;
  verify: jest.Mock;
} {
  return {
    signInWith: jest.fn().mockResolvedValue(true),
    verify: jest.fn().mockResolvedValue(true),
    ...over,
  } as EvmResumeHost & { signInWith: jest.Mock; verify: jest.Mock };
}

function notice(): HTMLElement | null {
  return document.querySelector("#evm-wallet-connect [data-notice]:not(#evm-app-error)");
}

function button(label: string): HTMLButtonElement {
  return Array.from(document.querySelectorAll("button")).find((b) => b.textContent === label)!;
}

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

beforeEach(() => {
  localStorage.clear();
  document.body.innerHTML = "";
  document.documentElement.classList.add("in-app");
});

describe("rememberEvmStep and forgetEvmStep", () => {
  it("keeps the step in the app (V1)", () => {
    rememberEvmStep(SIGN);
    expect(JSON.parse(localStorage.getItem(EVM_RESUME_KEY)!)).toEqual(SIGN);
    forgetEvmStep();
    expect(localStorage.getItem(EVM_RESUME_KEY)).toBeNull();
  });

  it("keeps nothing on the website", () => {
    document.documentElement.classList.remove("in-app");
    rememberEvmStep(SIGN);
    expect(localStorage.getItem(EVM_RESUME_KEY)).toBeNull();
  });

  it("does not throw on a blocked storage", () => {
    const target = { document, localStorage: blocked } as unknown as Window;
    expect(() => rememberEvmStep(SIGN, target)).not.toThrow();
    expect(() => forgetEvmStep(blocked)).not.toThrow();
  });
});

describe("takeEvmStep", () => {
  function stored(value: unknown) {
    localStorage.setItem(EVM_RESUME_KEY, typeof value === "string" ? value : JSON.stringify(value));
  }

  it("returns a sign step once", () => {
    stored(SIGN);
    expect(takeEvmStep(localStorage, PAGE, NOW)).toEqual(SIGN);
    expect(takeEvmStep(localStorage, PAGE, NOW)).toBeNull();
  });

  it("returns a connect step", () => {
    stored({ kind: "connect", url: PAGE, at: NOW });
    expect(takeEvmStep(localStorage, PAGE, NOW)).toEqual({ kind: "connect", url: PAGE, at: NOW });
  });

  it("leaves a fresh step for its own page", () => {
    stored(SIGN);
    expect(takeEvmStep(localStorage, "https://www.asastats.com/", NOW)).toBeNull();
    expect(localStorage.getItem(EVM_RESUME_KEY)).not.toBeNull();
  });

  it.each([
    ["too old", { at: NOW - 5 * 60 * 1000 - 1 }],
    ["from the future", { at: NOW + 1 }],
    ["without a time", { at: undefined }],
    ["without a page", { url: undefined, at: NOW }],
    ["of another kind", { kind: "pay" }],
    ["with a checksummed address", { address: "0xF74bbabffd0e455934b2b450ea391d59410cf361" }],
    ["with a short nonce", { nonce: "abc" }],
    ["with a markup prefix", { prefix: "<b>" }],
    ["with a short binding", { binding: "ab" }],
    ["with a foreign API base", { apiBase: "https://evil.example/api" }],
    ["with a non-string field", { address: 1 }],
    ["with a non-string nonce", { nonce: 1 }],
    ["with a non-string prefix", { prefix: 1 }],
    ["with a non-string binding", { binding: 1 }],
    ["with a non-string API base", { apiBase: 1 }],
  ])("refuses and drops a step %s (V6)", (_, change) => {
    stored({ ...SIGN, ...change });
    expect(takeEvmStep(localStorage, PAGE, NOW)).toBeNull();
    expect(localStorage.getItem(EVM_RESUME_KEY)).toBeNull();
  });

  it("drops unreadable JSON", () => {
    stored("{");
    expect(takeEvmStep(localStorage, PAGE, NOW)).toBeNull();
    expect(localStorage.getItem(EVM_RESUME_KEY)).toBeNull();
  });

  it.each([["nothing", null], ["a non-object", "1"]])("returns null for %s", (_, value) => {
    if (value !== null) stored(value);
    expect(takeEvmStep(localStorage, PAGE, NOW)).toBeNull();
  });
});

describe("sessionAddress and peerName", () => {
  it("returns the one address, lower-cased", () => {
    const upper = session({ namespaces: { eip155: { accounts: [`eip155:1:${ADDRESS.toUpperCase().replace("0X", "0x")}`] } } });
    expect(sessionAddress(upper)).toBe(ADDRESS);
  });

  it("counts one address on two chains as one", () => {
    const two = session({ namespaces: { eip155: { accounts: [`eip155:1:${ADDRESS}`, `eip155:137:${ADDRESS}`] } } });
    expect(sessionAddress(two)).toBe(ADDRESS);
  });

  it.each([
    ["no session", undefined],
    ["no eip155 accounts", session({ namespaces: {} })],
    ["two addresses", session({ namespaces: { eip155: { accounts: [`eip155:1:${ADDRESS}`, "eip155:1:0x" + "1".repeat(40)] } } })],
    ["a malformed address", session({ namespaces: { eip155: { accounts: ["eip155:1:0x12"] } } })],
  ])("returns null for %s (V2)", (_, value) => {
    expect(sessionAddress(value)).toBeNull();
  });

  it("names the wallet from its metadata, trimmed and short", () => {
    expect(peerName(session())).toBe("Trust Wallet");
    expect(peerName(session({ peer: { metadata: { name: ` ${"x".repeat(60)} ` } } }))).toHaveLength(40);
  });

  it.each([undefined, session({ peer: {} }), session({ peer: { metadata: { name: " " } } }), session({ peer: { metadata: { name: 1 } } })])(
    "falls back to Your wallet",
    (value) => {
      expect(peerName(value)).toBe("Your wallet");
    }
  );
});

describe("adoptSession", () => {
  it("keeps the provider's own session when the client has no other", () => {
    const own = provider();
    expect(adoptSession(own)).toBe(own.session);
    const same = provider({ stored: [session()] });
    expect(adoptSession(same)).toBe(same.session);
    expect(same.signer.createProviders).not.toHaveBeenCalled();
  });

  it("moves an older session aside for the newest", () => {
    const newer = session({ topic: "bbbbbbbb", expiry: 9 });
    const p = provider({ session: session({ expiry: 1 }), stored: [session({ expiry: 1 }), newer] });
    expect(adoptSession(p)).toBe(newer);
    expect(p.signer.createProviders).toHaveBeenCalled();
  });

  it("adopts the newest session the client stored after init", () => {
    const older = session({ topic: "aaaaaaaa", expiry: 1 });
    const newer = session({ topic: "bbbbbbbb", expiry: 2 });
    const p = provider({ session: undefined, stored: [newer, older, session({ topic: "cccccccc" })] });
    expect(adoptSession(p)).toBe(newer);
    expect(p.session).toBe(newer);
    expect(p.signer.createProviders).toHaveBeenCalled();
  });

  it("prefers a session with an expiry over one without", () => {
    const newer = session({ topic: "bbbbbbbb", expiry: 2 });
    const p = provider({ session: undefined, stored: [session({ topic: "aaaaaaaa" }), newer] });
    expect(adoptSession(p)).toBe(newer);
  });

  it("returns the adopted session even without a provider getter", () => {
    const newer = session({ topic: "bbbbbbbb" });
    const p = { session: undefined, signer: { client: { session: { getAll: () => [newer] } } } } as unknown as RestoredProvider;
    expect(adoptSession(p)).toBe(newer);
  });

  it("returns undefined when nothing is stored", () => {
    expect(adoptSession(provider({ session: undefined }))).toBeUndefined();
    const p = provider({ session: undefined });
    delete p.signer.client.session;
    expect(adoptSession(p)).toBeUndefined();
  });
});

describe("fixNamespace", () => {
  it("gives the rpc provider the session's methods when it lost them", () => {
    const p = provider();
    fixNamespace(p);
    expect(p.updateNamespace).toHaveBeenCalledWith(session().namespaces!.eip155);
  });

  it("leaves an rpc provider that has them", () => {
    const p = provider({ rpcMethods: ["personal_sign"] });
    fixNamespace(p);
    expect(p.updateNamespace).not.toHaveBeenCalled();
  });

  it("does nothing without an rpc provider or a session namespace", () => {
    const p = provider({ session: session({ namespaces: {} }) });
    fixNamespace(p);
    expect(p.updateNamespace).not.toHaveBeenCalled();
    delete p.signer.rpcProviders;
    expect(() => fixNamespace(p)).not.toThrow();
  });
});

describe("messageHex", () => {
  it("hex-encodes UTF-8", () => {
    expect(messageHex("A€")).toBe("0x41e282ac");
  });
});

describe("signedAnswer", () => {
  it("finds our answered request (V2)", () => {
    const record = signRecord();
    expect(signedAnswer(provider({ records: [record] }), SIGN)).toEqual({ signature: SIGNATURE, record });
  });

  it("matches the message and address case-insensitively", () => {
    const record = signRecord();
    const params = (record.request.params as { request: { params: string[] } }).request.params;
    params[0] = params[0].toUpperCase().replace("0X", "0x");
    params[1] = params[1].toUpperCase().replace("0X", "0x");
    expect(signedAnswer(provider({ records: [record] }), SIGN)).not.toBeNull();
  });

  it.each([
    ["on another topic", { topic: "ffffffff" }],
    ["of another method", { request: { method: "wc_sessionPropose" } }],
    ["for another inner method", { request: { method: "wc_sessionRequest", params: { request: { method: "eth_sign", params: [] } } } }],
    ["without inner params", { request: { method: "wc_sessionRequest", params: { request: { method: "personal_sign" } } } }],
    ["without params", { request: { method: "wc_sessionRequest" } }],
    ["for another message", { request: { method: "wc_sessionRequest", params: { request: { method: "personal_sign", params: ["0x00", ADDRESS] } } } }],
    ["for another address", { request: { method: "wc_sessionRequest", params: { request: { method: "personal_sign", params: [messageHex(SIGN.prefix + SIGN.nonce), "0x" + "1".repeat(40)] } } } }],
    ["unanswered", { response: undefined }],
    ["refused", { response: { error: { code: 5000 } } }],
    ["with a malformed signature", { response: { result: "0x12" } }],
    ["with a non-string result", { response: { result: 1 } }],
  ])("skips a record %s", (_, change) => {
    expect(signedAnswer(provider({ records: [signRecord(change as Partial<WcHistoryRecord>)] }), SIGN)).toBeNull();
  });

  it("finds nothing without a session", () => {
    expect(signedAnswer(provider({ session: undefined, records: [signRecord()] }), SIGN)).toBeNull();
  });
});

describe("forgetSignatures", () => {
  it("deletes the session's personal_sign records only (V3, E4)", () => {
    const other: WcHistoryRecord = { id: 2, topic: TOPIC, request: { method: "wc_sessionSettle" } };
    const foreign = signRecord({ id: 3, topic: "ffffffff" });
    const p = provider({ records: [signRecord(), other, foreign] });
    forgetSignatures(p);
    expect(p.signer.client.core.history.values.map((r) => r.id)).toEqual([2, 3]);
  });

  it("ignores providers that are not WalletConnect's", () => {
    expect(() => forgetSignatures({ request: jest.fn() })).not.toThrow();
    expect(() => forgetSignatures(null)).not.toThrow();
    expect(() => forgetSignatures({ session: { topic: TOPIC } })).not.toThrow();
  });
});

describe("waitFor", () => {
  it("returns the first truthy value", async () => {
    let calls = 0;
    await expect(waitFor(() => (++calls === 2 ? "yes" : null), 1000, 1)).resolves.toBe("yes");
  });

  it("gives up after the wait", async () => {
    await expect(waitFor(() => null, 5, 1)).resolves.toBeNull();
  });

  it("waits 20 s by default", async () => {
    jest.useFakeTimers();
    try {
      const pending = waitFor(() => null);
      await jest.advanceTimersByTimeAsync(20_500);
      await expect(pending).resolves.toBeNull();
    } finally {
      jest.useRealTimers();
    }
  });
});

describe("reveal", () => {
  function dialogPage(open = false) {
    document.body.innerHTML = `
      <a href="#modal-tab-wallet">Wallet</a>
      <dialog id="modalLogin" ${open ? "open" : ""}>
        <div id="modal-tab-wallet" class="modal-tab-panel">
          <div id="evm-wallet-connect"></div>
        </div>
      </dialog>`;
    const dialog = document.getElementById("modalLogin") as HTMLDialogElement;
    dialog.showModal = jest.fn(() => dialog.setAttribute("open", ""));
    return { dialog, el: document.getElementById("evm-wallet-connect")! };
  }

  it("opens the closed login dialog on the wallet tab", () => {
    const { dialog, el } = dialogPage();
    const tab = jest.fn((e: Event) => e.preventDefault());
    document.querySelector('[href="#modal-tab-wallet"]')!.addEventListener("click", tab);
    reveal(el);
    expect(dialog.showModal).toHaveBeenCalled();
    expect(tab).toHaveBeenCalled();
  });

  it("leaves an open dialog", () => {
    const { dialog, el } = dialogPage(true);
    reveal(el);
    expect(dialog.showModal).not.toHaveBeenCalled();
  });

  it("opens a dialog without a tab panel", () => {
    document.body.innerHTML = '<dialog><div id="evm-wallet-connect"></div></dialog>';
    const dialog = document.querySelector("dialog") as HTMLDialogElement;
    dialog.showModal = jest.fn();
    reveal(document.getElementById("evm-wallet-connect")!);
    expect(dialog.showModal).toHaveBeenCalled();
  });

  it("does nothing outside a dialog or without showModal", () => {
    expect(() => reveal(container())).not.toThrow();
    document.body.innerHTML = '<dialog><div id="evm-wallet-connect"></div></dialog>';
    (document.querySelector("dialog") as unknown as { showModal: unknown }).showModal = undefined;
    expect(() => reveal(document.getElementById("evm-wallet-connect")!)).not.toThrow();
  });
});

describe("sayEvm and ask", () => {
  it("reuses the hand-off notice, never the no-wallet banner", () => {
    const el = container();
    el.insertAdjacentHTML("beforeend", '<div data-notice="info">old</div>');
    expect(sayEvm(el, "<b>new</b>").textContent).toBe("<b>new</b>");
    expect(el.querySelectorAll("[data-notice]")).toHaveLength(2);
    expect(document.getElementById("evm-app-error")!.textContent).toBe("");
  });

  it("asks once and disables both buttons", async () => {
    const el = container();
    const yes = jest.fn().mockResolvedValue(undefined);
    const no = jest.fn().mockResolvedValue(undefined);
    ask(el, "Finish?", "Finish signing in", yes, no);
    button("Finish signing in").click();
    await flush();
    expect(yes).toHaveBeenCalledTimes(1);
    expect(no).not.toHaveBeenCalled();
    expect(notice()!.querySelector("button")).toBeNull();
  });

  it("runs no on Not now", async () => {
    const el = container();
    const yes = jest.fn().mockResolvedValue(undefined);
    const no = jest.fn().mockResolvedValue(undefined);
    ask(el, "Finish?", "Finish signing in", yes, no);
    button("Not now").click();
    await flush();
    expect(no).toHaveBeenCalledTimes(1);
    expect(yes).not.toHaveBeenCalled();
  });
});

describe("resumeEvm", () => {
  const CONNECT = { kind: "connect" as const, url: PAGE, at: NOW };

  it("replaces the hand-off notice left outside the container", async () => {
    const el = container();
    document.querySelector("main")!.innerHTML = '<div data-notice="info" data-wallet-handoff="evm">lost</div>';
    el.insertAdjacentHTML("beforeend", '<div data-notice="info" data-wallet-handoff="evm">inside</div>');
    await resumeEvm(el, host(), CONNECT, async () => provider(), 5);
    expect(document.querySelector("main [data-wallet-handoff]")).toBeNull();
    expect(el.querySelector("[data-wallet-handoff]")).not.toBeNull();
  });

  it("offers to finish a resumed connect and signs in with the restored session", async () => {
    const el = container();
    const p = provider();
    const h = host();
    await expect(resumeEvm(el, h, CONNECT, async () => p, 5)).resolves.toBe("offered-connect");
    expect(notice()!.textContent).toContain("Trust Wallet connected before your phone closed ASA Stats.");
    expect(p.updateNamespace).toHaveBeenCalled();
    expect(button("Finish signing in").hasAttribute("data-evm-handoff")).toBe(true);
    button("Finish signing in").click();
    expect(notice()!.textContent).toBe("Open Trust Wallet and sign the message.");
    await flush();
    expect(h.signInWith).toHaveBeenCalledWith(p, ADDRESS, "Trust Wallet");
    expect(p.disconnect).not.toHaveBeenCalled();
  });

  it("waits 20 s by default and finds a session at once", async () => {
    await expect(resumeEvm(container(), host(), CONNECT, async () => provider())).resolves.toBe("offered-connect");
  });

  it("finds a connect the wallet approved after the provider started", async () => {
    const el = container();
    const p = provider({ session: undefined });
    let calls = 0;
    p.signer.client.session = { getAll: () => (++calls > 2 ? [session()] : []) };
    await expect(resumeEvm(el, host(), CONNECT, async () => p, 3000)).resolves.toBe("offered-connect");
    expect(p.signer.createProviders).toHaveBeenCalled();
  });

  it("disconnects when the resumed connect's sign-in fails (V5)", async () => {
    const el = container();
    const p = provider();
    const h = host({ signInWith: jest.fn().mockResolvedValue(false) });
    await resumeEvm(el, h, CONNECT, async () => p, 5);
    button("Finish signing in").click();
    await flush();
    expect(p.disconnect).toHaveBeenCalled();
    expect(notice()!.textContent).toBe("That did not finish. Please connect again.");
  });

  it("disconnects on Not now (V5)", async () => {
    const el = container();
    const p = provider();
    await resumeEvm(el, host(), CONNECT, async () => p, 5);
    button("Not now").click();
    await flush();
    expect(p.disconnect).toHaveBeenCalled();
    expect(notice()).toBeNull();
  });

  it("survives a disconnect that throws", async () => {
    const el = container();
    const p = provider();
    p.disconnect.mockRejectedValue(new Error("gone"));
    await resumeEvm(el, host(), CONNECT, async () => p, 5);
    button("Not now").click();
    await flush();
    expect(p.disconnect).toHaveBeenCalled();
  });

  it("says the step was lost without a session", async () => {
    const el = container();
    const p = provider({ session: undefined });
    await expect(resumeEvm(el, host(), CONNECT, async () => p, 5)).resolves.toBe("lost");
    expect(notice()!.textContent).toContain("did not answer in time");
    expect(p.disconnect).not.toHaveBeenCalled();
  });

  it("disconnects a session with no usable address and says it was lost (V2)", async () => {
    const el = container();
    const p = provider({ session: session({ namespaces: {} }) });
    await expect(resumeEvm(el, host(), CONNECT, async () => p, 5)).resolves.toBe("lost");
    expect(p.disconnect).toHaveBeenCalled();
  });

  it("says the step was lost when WalletConnect will not start", async () => {
    const el = container();
    await expect(
      resumeEvm(el, host(), CONNECT, async () => {
        throw new Error("no relay");
      }, 5)
    ).resolves.toBe("lost");
  });

  it("offers to finish with the stored signature, then posts it and deletes it (V3, V4)", async () => {
    const el = container();
    const p = provider({ records: [signRecord()] });
    const h = host();
    await expect(resumeEvm(el, h, SIGN, async () => p, 5)).resolves.toBe("offered-sign");
    expect(notice()!.textContent).toContain("Trust Wallet signed before your phone closed ASA Stats.");
    expect(h.verify).not.toHaveBeenCalled();
    button("Finish signing in").click();
    await flush();
    expect(h.verify).toHaveBeenCalledWith(SIGN.apiBase, NONCE, SIGNATURE, BINDING);
    expect(p.signer.client.core.history.values).toHaveLength(0);
  });

  it("deletes the stored signature on Not now", async () => {
    const el = container();
    const p = provider({ records: [signRecord()] });
    const h = host();
    await resumeEvm(el, h, SIGN, async () => p, 5);
    button("Not now").click();
    await flush();
    expect(h.verify).not.toHaveBeenCalled();
    expect(p.signer.client.core.history.values).toHaveLength(0);
    expect(notice()).toBeNull();
  });

  it("offers a fresh sign-in when the session lived but no answer came", async () => {
    const el = container();
    const p = provider();
    const h = host();
    await expect(resumeEvm(el, h, SIGN, async () => p, 5)).resolves.toBe("offered-again");
    button("Sign in with Trust Wallet").click();
    await flush();
    expect(h.signInWith).toHaveBeenCalledWith(p, ADDRESS, "Trust Wallet");
    expect(notice()!.textContent).toBe("Open Trust Wallet and sign the message.");
  });

  it("says so when the fresh sign-in fails", async () => {
    const el = container();
    const h = host({ signInWith: jest.fn().mockResolvedValue(false) });
    await resumeEvm(el, h, SIGN, async () => provider(), 5);
    button("Sign in with Trust Wallet").click();
    await flush();
    expect(notice()!.textContent).toBe("That did not finish. Please connect again.");
  });

  it("does not mark the button that only posts a stored signature as a hand-off", async () => {
    await resumeEvm(container(), host(), SIGN, async () => provider({ records: [signRecord()] }), 5);
    expect(button("Finish signing in").hasAttribute("data-evm-handoff")).toBe(false);
  });

  it("offers a fresh sign-in, not the stored answer, for another address", async () => {
    const el = container();
    const other = "0x" + "2".repeat(40);
    const p = provider({
      session: session({ namespaces: { eip155: { accounts: [`eip155:1:${other}`] } } }),
      records: [signRecord()],
    });
    await expect(resumeEvm(el, host(), SIGN, async () => p, 5)).resolves.toBe("offered-again");
    button("Not now").click();
    await flush();
    expect(notice()).toBeNull();
    expect(p.disconnect).not.toHaveBeenCalled();
  });
});
