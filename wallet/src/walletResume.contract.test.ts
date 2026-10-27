/**
 * R7: the records storeConnection writes are read back by the pinned
 * use-wallet, its Pera and Defly adapters and their connect libraries.
 */

import { generateAccount } from "algosdk";
import { NetworkId, WalletManager } from "@txnlab/use-wallet";
import { pera } from "@txnlab/use-wallet-pera";
import { defly } from "@txnlab/use-wallet-defly";

import { storeConnection, type ConnectStep } from "./walletResume";

// Both publish only an "import" export; load the very files the adapters use
// (use-wallet-pera carries its own nested @perawallet/connect).
jest.mock(
  "@perawallet/connect",
  () =>
    jest.requireActual(
      `${process.cwd()}/node_modules/@txnlab/use-wallet-pera/node_modules/@perawallet/connect/dist/index.js`
    ),
  { virtual: true }
);
jest.mock(
  "@blockshake/defly-connect",
  () => jest.requireActual(`${process.cwd()}/node_modules/@blockshake/defly-connect/dist/index.js`),
  { virtual: true }
);

// Their connect modals animate with lottie, which needs a canvas jsdom lacks.
jest.mock("lottie-web", () => ({ __esModule: true, default: { loadAnimation: jest.fn() } }));
jest.mock("@evanhahn/lottie-web-light", () => ({ __esModule: true, default: { loadAnimation: jest.fn() } }));

/** The connector opens the bridge on resume; nothing may reach the network. */
class QuietSocket {
  static OPEN = 1;
  readyState = 0;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: (() => void) | null = null;
  constructor(public url: string) {}
  send() {}
  close() {}
  addEventListener() {}
  removeEventListener() {}
}

const ADDRESS = generateAccount().addr.toString();

function step(wallet: string): ConnectStep {
  return {
    kind: "connect",
    wallet,
    url: "https://www.asastats.com/accounts/login/",
    at: Date.now(),
    bridge: "https://wallet-connect-h.perawallet.app",
    key: "11".repeat(32),
    clientId: "b1c6b7a2-0000-4000-8000-000000000001",
    handshakeId: 1_800_000_000_000_001,
    handshakeTopic: "b1c6b7a2-0000-4000-8000-000000000002",
    clientMeta: { name: "ASA Stats", description: "", url: "https://www.asastats.com", icons: [] },
  };
}

beforeEach(() => {
  localStorage.clear();
  (globalThis as unknown as { WebSocket: unknown }).WebSocket = QuietSocket;
});

it.each([
  ["pera", () => pera()],
  ["defly", () => defly()],
])("use-wallet resumes a stored %s connect as connected", async (id, adapter) => {
  storeConnection(
    step(id),
    { accounts: [ADDRESS], chainId: 416001, peerId: "peer", peerMeta: { name: id } },
    localStorage
  );
  const manager = new WalletManager({ wallets: [adapter()], defaultNetwork: NetworkId.MAINNET });
  await manager.resumeSessions();
  const wallet = manager.getWallet(id)!;
  expect(wallet.isConnected).toBe(true);
  expect(wallet.accounts.map((a) => a.address)).toEqual([ADDRESS]);
  expect(manager.activeWallet?.id).toBe(id);
});
