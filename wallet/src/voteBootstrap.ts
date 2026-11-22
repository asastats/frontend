/**
 * @file Wires the DAO vote panel (`#id-dao-vote-panel`) to a wallet (docs/logbook.md).
 */

import { WalletManager } from "@txnlab/use-wallet";
import { waitForConfirmation as algoWaitForConfirmation } from "algosdk";
import { createWalletManager } from "./walletAdapters";
import { castVote, type VoteDeps, type VoteRequest } from "./voteBridge";

/** The panel's id; `daovoting/_vote_panel.html` renders it. */
export const PANEL = "#id-dao-vote-panel";
const DEFAULT_API_BASE = "/api/v2/wallet";
/** Rounds to wait for the vote to confirm. */
const CONFIRM_ROUNDS = 6;

/** What the panel calls, resolved from `window.asastatsVote` at click time. */
export interface VoteApi {
  /** Every account of every connected wallet. */
  accounts: () => string[];
  /** Connect the wallet `walletId`; resolves with its accounts. */
  connect: (walletId: string) => Promise<string[]>;
  /** Sign and submit one vote; resolves with the confirmed transaction id. */
  castVote: (req: VoteRequest) => Promise<string>;
}

declare global {
  interface Window {
    asastatsVote?: VoteApi;
  }
}

/** A supported wallet as `/wallets/` lists it. */
interface WalletDescriptor {
  id: string;
  name: string;
}

/**
 * Every account of every connected wallet.
 *
 * @param manager - Resumed wallet manager.
 * @returns Addresses.
 */
export function connectedAccounts(manager: WalletManager): string[] {
  return manager.wallets
    .filter((wallet) => wallet.isConnected)
    .flatMap((wallet) => wallet.accounts.map((account) => account.address));
}

/**
 * The {@link VoteDeps} of a resumed wallet manager.
 *
 * @param manager - Resumed wallet manager on the panel's network.
 * @returns Collaborators for {@link castVote}.
 */
export function buildVoteDeps(manager: WalletManager): VoteDeps {
  const algod = manager.algodClient;
  return {
    accounts: () => connectedAccounts(manager),
    useAccount: (address) => {
      const wallet = manager.wallets.find(
        (w) => w.isConnected && w.accounts.some((account) => account.address === address),
      );
      if (!wallet) {
        throw new Error(`Connect the wallet holding ${address} first`);
      }
      wallet.setActive();
      wallet.setActiveAccount(address);
    },
    signTransactions: (txns, indexesToSign) => manager.signTransactions(txns, indexesToSign),
    suggestedParams: () => algod.getTransactionParams().do(),
    submit: async (signed) => {
      const response = await algod.sendRawTransaction(signed).do();
      return (response as { txid?: string }).txid ?? (response as { txId?: string }).txId ?? "";
    },
    waitForConfirmation: async (txid) => {
      await algoWaitForConfirmation(algod, txid, CONFIRM_ROUNDS);
    },
  };
}

/**
 * The {@link VoteApi} published as `window.asastatsVote`.
 *
 * @param manager - Resumed wallet manager on the panel's network.
 * @returns The API.
 */
export function buildVoteApi(manager: WalletManager): VoteApi {
  const deps = buildVoteDeps(manager);
  return {
    accounts: deps.accounts,
    connect: async (walletId) => {
      const wallet = manager.getWallet(walletId);
      if (!wallet) {
        throw new Error(`Unknown wallet: ${walletId}`);
      }
      return (await wallet.connect()).map((account) => account.address);
    },
    castVote: (req) => castVote(req, deps),
  };
}

function shortAddress(address: string): string {
  return `${address.slice(0, 5)}…${address.slice(-5)}`;
}

function say(element: Element, selector: string, message: string): void {
  const target = element.querySelector(selector);
  if (target) {
    target.textContent = message;
  }
}

/**
 * Show which accounts are connected and mark each seat card `data-vote-connected`.
 *
 * @param panel - The panel.
 * @param accounts - Connected addresses.
 */
export function showAccounts(panel: HTMLElement, accounts: string[]): void {
  say(
    panel,
    "[data-vote-accounts]",
    accounts.length
      ? `Connected in this browser: ${accounts.map(shortAddress).join(", ")}`
      : "No wallet is connected in this browser.",
  );
  panel.querySelectorAll<HTMLElement>("[data-vote-seat]").forEach((card) => {
    card.dataset.voteConnected = String(accounts.includes(card.dataset.voteSeat || ""));
  });
}

/**
 * One "Connect <wallet>" button per supported wallet, into `[data-vote-wallets]`.
 *
 * @param doc - Document creating the buttons.
 * @param panel - The panel.
 * @param wallets - Supported wallets.
 */
export function renderWallets(doc: Document, panel: HTMLElement, wallets: WalletDescriptor[]): void {
  const box = panel.querySelector("[data-vote-wallets]");
  if (!box) {
    return;
  }
  box.replaceChildren(
    ...wallets.map((wallet) => {
      const button = doc.createElement("button");
      button.type = "button";
      button.className = "btn btn-sm btn-outline";
      button.dataset.voteConnect = wallet.id;
      button.textContent = `Connect ${wallet.name}`;
      return button;
    }),
  );
}

/**
 * The vote a seat card's option button asks for.
 *
 * @param panel - The panel carrying the dApp ids, session and method.
 * @param card - The seat card.
 * @param option - Option index.
 * @returns The request.
 */
export function voteRequest(panel: HTMLElement, card: HTMLElement, option: number): VoteRequest {
  return {
    seat: card.dataset.voteSeat || "",
    appId: Number(panel.dataset.appId),
    permissionAppId: Number(panel.dataset.permissionAppId),
    sessionId: Number(panel.dataset.sessionId),
    option,
    method: panel.dataset.voteMethod || "",
  };
}

/**
 * Cast the vote of the clicked option button's card; report in its `[data-vote-status]`.
 *
 * @param panel - The panel.
 * @param button - The clicked `button[data-vote-option]`.
 */
export async function onVote(panel: HTMLElement, button: HTMLButtonElement): Promise<void> {
  const card = button.closest<HTMLElement>("[data-vote-seat]");
  if (!card) {
    return;
  }
  const api = window.asastatsVote;
  if (!api) {
    say(card, "[data-vote-status]", "The wallet is still loading. Try again in a moment.");
    return;
  }
  const option = Number(button.dataset.voteOption);
  const buttons = card.querySelectorAll<HTMLButtonElement>("button[data-vote-option]");
  buttons.forEach((b) => (b.disabled = true));
  say(card, "[data-vote-status]", "Waiting for your wallet to sign…");
  try {
    const txid = await api.castVote(voteRequest(panel, card, option));
    card.dataset.voteSent = String(option);
    say(
      card,
      "[data-vote-status]",
      `Vote for Option ${option} confirmed in transaction ${txid}. The ballots below update within a minute.`,
    );
  } catch (error) {
    say(card, "[data-vote-status]", error instanceof Error ? error.message : String(error));
  } finally {
    buttons.forEach((b) => (b.disabled = false));
  }
}

/**
 * Connect the clicked wallet button's wallet, then refresh the connected accounts.
 *
 * @param panel - The panel.
 * @param button - The clicked `button[data-vote-connect]`.
 */
export async function onConnect(panel: HTMLElement, button: HTMLButtonElement): Promise<void> {
  const api = window.asastatsVote;
  if (!api) {
    return;
  }
  try {
    await api.connect(button.dataset.voteConnect || "");
    showAccounts(panel, api.accounts());
  } catch (error) {
    say(panel, "[data-vote-accounts]", error instanceof Error ? error.message : String(error));
  }
}

/**
 * Bind the panel's buttons, then build the wallet manager and publish `window.asastatsVote`.
 *
 * A no-op without the panel or when already bound. A `window.asastatsVote` set
 * before this runs is kept (the functional tests install a stub).
 *
 * @param doc - Document to query.
 */
export async function initVotePanel(doc: Document = document): Promise<void> {
  const panel = doc.querySelector<HTMLElement>(PANEL);
  if (!panel || panel.dataset.voteBound) {
    return;
  }
  panel.dataset.voteBound = "true";
  panel.addEventListener("click", (event: Event) => {
    const target = event.target as HTMLElement;
    const vote = target.closest<HTMLButtonElement>("button[data-vote-option]");
    if (vote) {
      event.preventDefault();
      void onVote(panel, vote);
      return;
    }
    const connect = target.closest<HTMLButtonElement>("button[data-vote-connect]");
    if (connect) {
      event.preventDefault();
      void onConnect(panel, connect);
    }
  });

  try {
    const response = await fetch(`${panel.dataset.apiBase || DEFAULT_API_BASE}/wallets/`);
    if (!response.ok) {
      throw new Error("Failed to load supported wallets");
    }
    const wallets: WalletDescriptor[] = await response.json();
    const manager = createWalletManager(wallets, panel.dataset.network || "mainnet");
    await manager.resumeSessions();
    window.asastatsVote = window.asastatsVote || buildVoteApi(manager);
    renderWallets(doc, panel, wallets.filter((w) => manager.getWallet(w.id)));
    showAccounts(panel, window.asastatsVote.accounts());
  } catch (error) {
    console.error("Error loading the wallet:", error);
    say(panel, "[data-vote-accounts]", "The wallet could not be loaded on this page.");
  }
  window.dispatchEvent(new CustomEvent("asastats:vote-ready"));
}
