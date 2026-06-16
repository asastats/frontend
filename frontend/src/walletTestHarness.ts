/**
 * TEST-ONLY mock wallet harness.
 *
 * Loaded only when the page sets `window.__WALLET_TEST__` (the template emits it
 * solely under `settings.WALLET_TEST_MODE`, off in production). It exposes
 * `window.__installMockWallet(mnemonic, apiBase?)`, which a Selenium test calls
 * to drive the real {@link WalletComponent} without a browser extension.
 *
 * Why a custom mock rather than use-wallet's Mnemonic wallet: the library's
 * Mnemonic wallet calls `checkMainnet()` in `connect()` and refuses to run on
 * MainNet, and asastats pins MainNet (the backend rejects a TestNet genesis).
 * This harness instead signs a real 0-ALGO self-payment built with MainNet
 * suggested params, so the backend's signature + genesis checks run unchanged
 * and the test is genuinely end to end (the signed txn is never broadcast).
 *
 * Security: the signature only proves control of the supplied throwaway key, and
 * the verify endpoint still authorizes only the profile's own address. The
 * harness is never loaded when the flag is absent.
 */
import algosdk from "algosdk";

import { WalletComponent } from "./walletComponent";

/** MainNet genesis id/hash, so the built txn passes the backend network pin. */
const MAINNET_GENESIS_ID = "mainnet-v1.0";
const MAINNET_GENESIS_HASH_B64 = "wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=";

/** Decode a base64 string to the byte array algosdk expects for genesisHash. */
function genesisHashBytes(): Uint8Array {
  return Uint8Array.from(atob(MAINNET_GENESIS_HASH_B64), (c) => c.charCodeAt(0));
}

/** Build the `#wallet-mock` card the WalletComponent binds to, if not present. */
function ensureMockCard(): HTMLElement {
  let card = document.getElementById("wallet-mock");
  if (card) return card;
  card = document.createElement("div");
  card.id = "wallet-mock";
  card.innerHTML = `
    <h4>Mock</h4>
    <button id="connect-button-mock" type="button">Connect</button>
    <button id="set-active-button-mock" type="button" style="display:none">Set active</button>
    <button id="disconnect-button-mock" type="button" style="display:none">Disconnect</button>
    <select class="browser-default"></select>
    <button id="auth-button-mock" type="button" style="display:none">Authorize address</button>
  `;
  (document.getElementById("wallet-connect") || document.body).appendChild(card);
  return card;
}

/**
 * Build a minimal fake `BaseWallet` whose `signTransactions` produces a real
 * Ed25519 signature using the supplied account.
 *
 * @param acct - algosdk account derived from the test mnemonic
 */
function makeFakeWallet(acct: algosdk.Account) {
  const address = acct.addr.toString();
  const listeners: Array<() => void> = [];
  const emit = () => listeners.forEach((l) => l());

  const wallet: any = {
    id: "mock",
    isConnected: false,
    isActive: false,
    accounts: [] as any[],
    activeAccount: null as any,
    subscribe(cb: () => void) {
      listeners.push(cb);
      return () => listeners.splice(listeners.indexOf(cb), 1);
    },
    async connect() {
      const acctEntry = { name: "Mock Account", address };
      Object.assign(wallet, {
        isConnected: true,
        accounts: [acctEntry],
        activeAccount: acctEntry,
      });
      emit();
      return [acctEntry];
    },
    async disconnect() {
      Object.assign(wallet, {
        isConnected: false,
        isActive: false,
        accounts: [],
        activeAccount: null,
      });
      emit();
    },
    async setActive() {
      wallet.isActive = true;
      emit();
    },
    async setActiveAccount(addr: string) {
      wallet.activeAccount = { name: "Mock Account", address: addr };
      emit();
    },
    async signTransactions(txns: Uint8Array[]) {
      // Genuine signature: decode the unsigned txn the component built and sign
      // it with the test key. Returns msgpack-encoded signed-txn bytes.
      const unsigned = algosdk.decodeUnsignedTransaction(txns[0]);
      return [unsigned.signTxn(acct.sk)];
    },
  };
  return wallet;
}

/** Fake manager exposing only `algodClient.getTransactionParams().do()`. */
function makeFakeManager() {
  return {
    algodClient: {
      getTransactionParams: () => ({
        do: async () => ({
          fee: 0,
          minFee: 1000,
          flatFee: true,
          firstValid: 1,
          lastValid: 1000,
          genesisID: MAINNET_GENESIS_ID,
          genesisHash: genesisHashBytes(),
        }),
      }),
    },
  };
}

/** Install the harness, exposing the global the Selenium test calls. */
export function install() {
  (window as any).__installMockWallet = (
    testMnemonic: string,
    apiBase = "/api/v2/wallet"
  ) => {
    const acct = algosdk.mnemonicToSecretKey(testMnemonic);
    const card = ensureMockCard();
    const component = new WalletComponent(
      makeFakeWallet(acct) as any,
      makeFakeManager() as any,
      apiBase
    );
    component.bind(card);
    return acct.addr.toString();
  };
}
