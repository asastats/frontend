/**
 * @file The footer's "App lock" entry: opens the app's native lock settings.
 *
 * Hidden until the shell is known to have the AppLock plugin, which older app
 * builds do not. Design: capacitor/O2-BIOMETRIC-LOCK-DESIGN.md.
 */

import { Capacitor, registerPlugin } from "@capacitor/core";

/** The one call pages have; the switch and its prompt are native. */
export interface AppLockPlugin {
  openSettings(): Promise<void>;
}

export const AppLock = registerPlugin<AppLockPlugin>("AppLock");

/** base.html's footer entry. */
const ENTRY = "[data-app-lock-settings]";

/**
 * Show the entry and open the native settings on a tap, if the shell has the plugin.
 *
 * @param doc - the document holding the entry.
 * @returns whether the entry was shown.
 */
export function installAppLock(doc: Document = document): boolean {
  if (!Capacitor.isPluginAvailable("AppLock")) return false;
  const entries = doc.querySelectorAll<HTMLElement>(ENTRY);
  entries.forEach((entry) => {
    entry.hidden = false;
    entry.addEventListener("click", (event) => {
      event.preventDefault();
      void AppLock.openSettings();
    });
  });
  return entries.length > 0;
}
