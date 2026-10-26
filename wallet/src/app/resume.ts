/**
 * @file Wake the wallets' sockets when the app comes back from the background.
 *
 * Pera and Defly Connect wait for the wallet's answer on a WalletConnect v1
 * socket, which a frozen app can lose without a `close` event; their transport
 * reconnects on `online`. See docs/logbook.md.
 */

import { App } from "@capacitor/app";

/**
 * Fire `online` on every resume, so a dead wallet socket is replaced.
 *
 * @param target - the window the transports listen on.
 */
export function installResume(target: Window = window): void {
  void App.addListener("resume", () => {
    target.dispatchEvent(new Event("online"));
  });
}
