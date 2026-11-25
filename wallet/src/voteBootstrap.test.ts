/**
 * @jest-environment jsdom
 */

const createWalletManager = jest.fn();
jest.mock("./walletAdapters", () => ({
  createWalletManager: (...a: unknown[]) => createWalletManager(...a),
}));

const algoWaitForConfirmation = jest.fn().mockResolvedValue(undefined);
jest.mock("algosdk", () => ({
  ...jest.requireActual("algosdk"),
  waitForConfirmation: (...a: unknown[]) => algoWaitForConfirmation(...a),
}));

const castVote = jest.fn().mockResolvedValue("VOTED");
jest.mock("./voteBridge", () => ({
  castVote: (...a: unknown[]) => castVote(...a),
}));

import {
  buildVoteApi,
  buildVoteDeps,
  connectedAccounts,
  initVotePanel,
  markVoted,
  onConnect,
  onDisconnect,
  onVote,
  renderWallets,
  showAccounts,
  voteRequest,
  type VoteApi,
} from "./voteBootstrap";

const SEAT = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M";
const OTHER = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU";

function wallet(id: string, connected: boolean, addresses: string[]) {
  return {
    id,
    isConnected: connected,
    accounts: addresses.map((address) => ({ address })),
    setActive: jest.fn(),
    setActiveAccount: jest.fn(),
    connect: jest.fn().mockResolvedValue(addresses.map((address) => ({ address }))),
  };
}

function algod(sent: Record<string, string> = { txid: "T1" }) {
  return {
    getTransactionParams: () => ({ do: jest.fn().mockResolvedValue({ minFee: 1000n }) }),
    sendRawTransaction: jest.fn(() => ({ do: jest.fn().mockResolvedValue(sent) })),
  };
}

function manager(wallets: ReturnType<typeof wallet>[], client = algod()) {
  return {
    wallets,
    algodClient: client,
    signTransactions: jest.fn().mockResolvedValue([Uint8Array.of(1)]),
    getWallet: (id: string) => wallets.find((w) => w.id === id),
    resumeSessions: jest.fn().mockResolvedValue(undefined),
    disconnect: jest.fn().mockResolvedValue(undefined),
  } as any;
}

const PANEL_HTML = `
  <section id="id-dao-vote-panel" data-app-id="775947805" data-permission-app-id="750094865"
           data-session-id="2" data-network="testnet" data-vote-method="vote(uint64,uint64)void">
    <div data-vote-wallets></div>
    <p data-vote-accounts></p>
    <div data-vote-seat="${SEAT}">
      <button type="button" data-vote-option="0">Option 0</button>
      <button type="button" data-vote-option="1"><span>Option 1</span></button>
      <p data-vote-status></p>
    </div>
    <div data-vote-seat="${OTHER}"><p data-vote-status></p></div>
  </section>`;

function panel(): HTMLElement {
  document.body.innerHTML = PANEL_HTML;
  return document.querySelector<HTMLElement>("#id-dao-vote-panel")!;
}

function status(seat = SEAT): string {
  return document.querySelector(`[data-vote-seat="${seat}"] [data-vote-status]`)!.textContent || "";
}

function api(overrides: Partial<VoteApi> = {}): VoteApi {
  return {
    accounts: jest.fn(() => [SEAT]),
    connect: jest.fn().mockResolvedValue([SEAT]),
    disconnect: jest.fn().mockResolvedValue(undefined),
    castVote: jest.fn().mockResolvedValue("TX9"),
    ...overrides,
  };
}

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

beforeEach(() => {
  delete window.asastatsVote;
  document.body.innerHTML = "";
  jest.clearAllMocks();
});

describe("connectedAccounts", () => {
  it("lists every account of every connected wallet", () => {
    const m = manager([wallet("pera", true, [SEAT, OTHER]), wallet("defly", false, ["X"])]);
    expect(connectedAccounts(m)).toEqual([SEAT, OTHER]);
  });
});

describe("buildVoteDeps", () => {
  it("selects the wallet and account holding the seat", () => {
    const pera = wallet("pera", true, [OTHER]);
    const defly = wallet("defly", true, [SEAT]);
    buildVoteDeps(manager([pera, defly])).useAccount(SEAT);
    expect(defly.setActive).toHaveBeenCalled();
    expect(defly.setActiveAccount).toHaveBeenCalledWith(SEAT);
    expect(pera.setActive).not.toHaveBeenCalled();
  });

  it("refuses an account no connected wallet holds", () => {
    const deps = buildVoteDeps(manager([wallet("pera", false, [SEAT])]));
    expect(() => deps.useAccount(SEAT)).toThrow(`Connect the wallet holding ${SEAT} first`);
  });

  it("signs through the manager and reads algod", async () => {
    const m = manager([wallet("pera", true, [SEAT])]);
    const deps = buildVoteDeps(m);
    expect(deps.accounts()).toEqual([SEAT]);
    await expect(deps.signTransactions([Uint8Array.of(5)], [0])).resolves.toEqual([Uint8Array.of(1)]);
    expect(m.signTransactions).toHaveBeenCalledWith([Uint8Array.of(5)], [0]);
    await expect(deps.suggestedParams()).resolves.toEqual({ minFee: 1000n });
    await expect(deps.submit([Uint8Array.of(1)])).resolves.toBe("T1");
    await deps.waitForConfirmation("T1");
    expect(algoWaitForConfirmation).toHaveBeenCalledWith(m.algodClient, "T1", 6);
  });

  it.each([
    [{ txId: "OLD" }, "OLD"],
    [{}, ""],
  ])("reads the submitted id from %p", async (sent, expected) => {
    const deps = buildVoteDeps(manager([], algod(sent as Record<string, string>)));
    await expect(deps.submit([Uint8Array.of(1)])).resolves.toBe(expected);
  });
});

describe("buildVoteApi", () => {
  it("connects a wallet and casts votes through castVote", async () => {
    const pera = wallet("pera", true, [SEAT]);
    const voteApi = buildVoteApi(manager([pera]));
    await expect(voteApi.connect("pera")).resolves.toEqual([SEAT]);
    expect(voteApi.accounts()).toEqual([SEAT]);
    const req = { seat: SEAT } as any;
    await expect(voteApi.castVote(req)).resolves.toBe("VOTED");
    expect(castVote).toHaveBeenCalledWith(req, expect.objectContaining({ accounts: expect.any(Function) }));
  });

  it("disconnects through the manager", async () => {
    const m = manager([]);
    await buildVoteApi(m).disconnect();
    expect(m.disconnect).toHaveBeenCalled();
  });

  it("refuses an unknown wallet", async () => {
    await expect(buildVoteApi(manager([])).connect("exodus")).rejects.toThrow("Unknown wallet: exodus");
  });
});

describe("panel rendering", () => {
  it("shows the connected accounts and marks each seat card", () => {
    const p = panel();
    showAccounts(p, [SEAT]);
    expect(p.querySelector("[data-vote-accounts]")!.textContent).toBe(
      "Connected in this browser: OGRUN…CEN2M",
    );
    const cards = p.querySelectorAll<HTMLElement>("[data-vote-seat]");
    expect([cards[0].dataset.voteConnected, cards[1].dataset.voteConnected]).toEqual(["true", "false"]);
    showAccounts(p, []);
    expect(p.querySelector("[data-vote-accounts]")!.textContent).toBe(
      "No wallet is connected in this browser.",
    );
  });

  it("tolerates a panel without the accounts line or a seat attribute", () => {
    document.body.innerHTML = '<section id="p"><div data-vote-seat></div></section>';
    const p = document.querySelector<HTMLElement>("#p")!;
    showAccounts(p, [SEAT]);
    expect(p.querySelector<HTMLElement>("[data-vote-seat]")!.dataset.voteConnected).toBe("false");
  });

  it("renders one connect button per wallet, as text", () => {
    const p = panel();
    renderWallets(document, p, [
      { id: "pera", name: "Pera" },
      { id: "x", name: "<b>X</b>" },
    ]);
    const buttons = p.querySelectorAll<HTMLButtonElement>("[data-vote-wallets] button");
    expect(Array.from(buttons, (b) => [b.dataset.voteConnect, b.textContent, b.type])).toEqual([
      ["pera", "Connect Pera", "button"],
      ["x", "Connect <b>X</b>", "button"],
      [undefined, "Disconnect", "button"],
    ]);
    const disconnect = p.querySelector<HTMLButtonElement>("button[data-vote-disconnect]")!;
    expect(disconnect.hidden).toBe(true);
    showAccounts(p, [SEAT]);
    expect(disconnect.hidden).toBe(false);
    showAccounts(p, []);
    expect(disconnect.hidden).toBe(true);
  });

  it("renders no wallet buttons without their container", () => {
    document.body.innerHTML = '<section id="p"></section>';
    const p = document.querySelector<HTMLElement>("#p")!;
    renderWallets(document, p, [{ id: "pera", name: "Pera" }]);
    expect(p.innerHTML).toBe("");
  });

  it("builds the request from the panel and the card", () => {
    const p = panel();
    const card = p.querySelector<HTMLElement>("[data-vote-seat]")!;
    expect(voteRequest(p, card, 1)).toEqual({
      seat: SEAT,
      appId: 775947805,
      permissionAppId: 750094865,
      sessionId: 2,
      option: 1,
      method: "vote(uint64,uint64)void",
    });
    document.body.innerHTML = '<section id="p"><div id="c"></div></section>';
    const bare = voteRequest(
      document.querySelector<HTMLElement>("#p")!,
      document.querySelector<HTMLElement>("#c")!,
      0,
    );
    expect([bare.seat, bare.method]).toEqual(["", ""]);
  });
});

describe("markVoted", () => {
  it("shows the option as the vote and relabels the buttons", () => {
    document.body.innerHTML = `
      <div data-vote-seat="S">
        <span data-vote-current>not voted</span>
        <button class="btn" data-vote-option="0">Vote Option 0</button>
        <button class="btn btn-outline" data-vote-option="1" data-vote-chosen>Option 1 (your vote)</button>
      </div>`;
    const card = document.querySelector<HTMLElement>("[data-vote-seat]")!;
    markVoted(card, 0);
    const current = card.querySelector<HTMLElement>("[data-vote-current]")!;
    expect(current.textContent).toBe("Option 0");
    expect(current.classList.contains("badge-success")).toBe(true);
    const buttons = Array.from(card.querySelectorAll<HTMLButtonElement>("button"));
    expect(buttons.map((b) => b.textContent)).toEqual(["Option 0 (your vote)", "Change to Option 1"]);
    expect(buttons.map((b) => b.classList.contains("btn-outline"))).toEqual([true, false]);
    expect(buttons.map((b) => b.hasAttribute("data-vote-chosen"))).toEqual([true, false]);
  });

  it("tolerates a card without the vote line", () => {
    document.body.innerHTML = '<div data-vote-seat="S"><button data-vote-option="2">x</button></div>';
    const card = document.querySelector<HTMLElement>("[data-vote-seat]")!;
    markVoted(card, 2);
    expect(card.querySelector("button")!.textContent).toBe("Option 2 (your vote)");
  });
});

describe("onVote", () => {
  it("casts the vote and reports the transaction", async () => {
    const p = panel();
    window.asastatsVote = api();
    const button = p.querySelector<HTMLButtonElement>('[data-vote-option="1"]')!;
    const pending = onVote(p, button);
    expect(button.disabled).toBe(true);
    expect(status()).toBe("Waiting for your wallet to sign…");
    await pending;
    expect(window.asastatsVote.castVote).toHaveBeenCalledWith(expect.objectContaining({ seat: SEAT, option: 1 }));
    expect(status()).toBe(
      "Vote for Option 1 confirmed in transaction TX9. The ballots below update within a minute.",
    );
    expect(p.querySelector<HTMLElement>("[data-vote-seat]")!.dataset.voteSent).toBe("1");
    expect(button.disabled).toBe(false);
  });

  it.each([
    [new Error("Voting has ended"), "Voting has ended"],
    ["plain", "plain"],
  ])("reports a failed vote (%p)", async (failure, message) => {
    const p = panel();
    window.asastatsVote = api({ castVote: jest.fn().mockRejectedValue(failure) });
    const button = p.querySelector<HTMLButtonElement>('[data-vote-option="0"]')!;
    await onVote(p, button);
    expect(status()).toBe(message);
    expect(button.disabled).toBe(false);
  });

  it("asks to wait while the wallet loads", async () => {
    const p = panel();
    await onVote(p, p.querySelector<HTMLButtonElement>('[data-vote-option="0"]')!);
    expect(status()).toBe("The wallet is still loading. Try again in a moment.");
  });

  it("ignores a button outside a seat card", async () => {
    const p = panel();
    window.asastatsVote = api();
    const loose = document.createElement("button");
    p.appendChild(loose);
    await onVote(p, loose);
    expect(window.asastatsVote.castVote).not.toHaveBeenCalled();
  });

  it("does not fail on a card without a status line", async () => {
    document.body.innerHTML =
      '<section id="p"><div data-vote-seat="S"><button data-vote-option="0"></button></div></section>';
    const p = document.querySelector<HTMLElement>("#p")!;
    window.asastatsVote = api();
    await onVote(p, p.querySelector<HTMLButtonElement>("button")!);
    expect(window.asastatsVote.castVote).toHaveBeenCalled();
  });
});

describe("onConnect", () => {
  function connectButton(id: string | null) {
    const button = document.createElement("button");
    if (id !== null) button.dataset.voteConnect = id;
    return button;
  }

  it("connects and refreshes the accounts", async () => {
    const p = panel();
    window.asastatsVote = api();
    await onConnect(p, connectButton("pera"));
    expect(window.asastatsVote.connect).toHaveBeenCalledWith("pera");
    expect(p.querySelector<HTMLElement>("[data-vote-seat]")!.dataset.voteConnected).toBe("true");
  });

  it.each([
    [new Error("Connection rejected"), "Connection rejected"],
    ["closed", "closed"],
  ])("reports a failed connect (%p)", async (failure, message) => {
    const p = panel();
    window.asastatsVote = api({ connect: jest.fn().mockRejectedValue(failure) });
    await onConnect(p, connectButton(null));
    expect(window.asastatsVote.connect).toHaveBeenCalledWith("");
    expect(p.querySelector("[data-vote-accounts]")!.textContent).toBe(message);
  });

  it("does nothing before the wallet loads", async () => {
    const p = panel();
    await expect(onConnect(p, connectButton("pera"))).resolves.toBeUndefined();
  });
});

describe("onDisconnect", () => {
  it("disconnects and refreshes the accounts", async () => {
    const p = panel();
    window.asastatsVote = api({ accounts: jest.fn(() => []) });
    await onDisconnect(p);
    expect(window.asastatsVote.disconnect).toHaveBeenCalled();
    expect(p.querySelector("[data-vote-accounts]")!.textContent).toBe(
      "No wallet is connected in this browser.",
    );
  });

  it.each([
    [new Error("Disconnect failed"), "Disconnect failed"],
    ["closed", "closed"],
  ])("reports a failed disconnect (%p)", async (failure, message) => {
    const p = panel();
    window.asastatsVote = api({ disconnect: jest.fn().mockRejectedValue(failure) });
    await onDisconnect(p);
    expect(p.querySelector("[data-vote-accounts]")!.textContent).toBe(message);
  });

  it("does nothing before the wallet loads", async () => {
    await expect(onDisconnect(panel())).resolves.toBeUndefined();
  });
});

describe("initVotePanel", () => {
  const fetchMock = jest.fn();
  beforeEach(() => {
    (global as any).fetch = fetchMock;
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => [
        { id: "pera", name: "Pera" },
        { id: "exodus", name: "Exodus" },
      ],
    });
  });

  it("does nothing without the panel", async () => {
    await initVotePanel(document);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("builds the manager on the panel's network and publishes the API", async () => {
    const p = panel();
    const m = manager([wallet("pera", true, [SEAT])]);
    createWalletManager.mockReturnValue(m);
    const ready = jest.fn();
    window.addEventListener("asastats:vote-ready", ready);
    await initVotePanel(document);
    window.removeEventListener("asastats:vote-ready", ready);
    expect(fetchMock).toHaveBeenCalledWith("/api/v2/wallet/wallets/");
    expect(createWalletManager).toHaveBeenCalledWith(
      [
        { id: "pera", name: "Pera" },
        { id: "exodus", name: "Exodus" },
      ],
      "testnet",
    );
    expect(m.resumeSessions).toHaveBeenCalled();
    expect(window.asastatsVote!.accounts()).toEqual([SEAT]);
    expect(
      Array.from(p.querySelectorAll("[data-vote-wallets] button"), (b) => b.textContent),
    ).toEqual(["Connect Pera", "Disconnect"]);
    expect(p.querySelector<HTMLButtonElement>("button[data-vote-disconnect]")!.hidden).toBe(false);
    expect(p.querySelector<HTMLElement>("[data-vote-seat]")!.dataset.voteConnected).toBe("true");
    expect(ready).toHaveBeenCalled();

    await initVotePanel(document); // bound once
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("keeps an API published before it and defaults the network and API base", async () => {
    const p = panel();
    delete p.dataset.network;
    p.dataset.apiBase = "/api/x";
    const stub = api();
    window.asastatsVote = stub;
    createWalletManager.mockReturnValue(manager([]));
    await initVotePanel(document);
    expect(fetchMock).toHaveBeenCalledWith("/api/x/wallets/");
    expect(createWalletManager).toHaveBeenCalledWith(expect.anything(), "mainnet");
    expect(window.asastatsVote).toBe(stub);
  });

  it("says so when the wallet cannot be loaded", async () => {
    const p = panel();
    fetchMock.mockResolvedValue({ ok: false });
    const error = jest.spyOn(console, "error").mockImplementation(() => {});
    await initVotePanel(document);
    expect(error).toHaveBeenCalled();
    error.mockRestore();
    expect(p.querySelector("[data-vote-accounts]")!.textContent).toBe(
      "The wallet could not be loaded on this page.",
    );
  });

  it("routes clicks to voting and connecting", async () => {
    const p = panel();
    createWalletManager.mockReturnValue(manager([wallet("pera", false, [])]));
    const stub = api();
    window.asastatsVote = stub;
    await initVotePanel(document);

    p.querySelector<HTMLElement>('[data-vote-option="1"] span')!.click();
    await flush();
    expect(stub.castVote).toHaveBeenCalledWith(expect.objectContaining({ option: 1 }));

    p.querySelector<HTMLButtonElement>("[data-vote-wallets] button")!.click();
    await flush();
    expect(stub.connect).toHaveBeenCalledWith("pera");

    p.querySelector<HTMLButtonElement>("button[data-vote-disconnect]")!.click();
    await flush();
    expect(stub.disconnect).toHaveBeenCalledTimes(1);

    p.querySelector<HTMLElement>("[data-vote-accounts]")!.click();
    await flush();
    expect(stub.castVote).toHaveBeenCalledTimes(1);
    expect(stub.connect).toHaveBeenCalledTimes(1);
  });
});
