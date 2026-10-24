/**
 * @file Hide the native splash once the page can be seen.
 *
 * The shell also auto-hides it after a few seconds, so a page that never runs
 * this still clears it (mobile/capacitor.config.ts).
 */

import { SplashScreen } from "@capacitor/splash-screen";

/**
 * Hide the splash now if the document is parsed, otherwise on DOMContentLoaded.
 *
 * @param doc - the document to wait for.
 */
export function installSplash(doc: Document = document): void {
  const hide = () => {
    void SplashScreen.hide();
  };
  if (doc.readyState === "loading") {
    doc.addEventListener("DOMContentLoaded", hide, { once: true });
  } else {
    hide();
  }
}
