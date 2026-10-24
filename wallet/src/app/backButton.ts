/**
 * @file Android's back button: close what is open, then go back, then leave.
 *
 * Without a listener the app exits on the first press. `minimizeApp` rather
 * than `exitApp`, so the page is still there when the user returns.
 */

import { App, type BackButtonListenerEvent } from "@capacitor/app";

/**
 * Close the topmost open dialog or disclosure menu.
 *
 * @param doc - the document to search.
 * @returns whether something was closed.
 */
export function closeOverlay(doc: Document = document): boolean {
  const dialogs = doc.querySelectorAll<HTMLDialogElement>("dialog[open]");
  const dialog = dialogs[dialogs.length - 1];
  if (dialog) {
    dialog.close();
    return true;
  }
  const menu = doc.querySelector<HTMLDetailsElement>("details.dropdown[open]");
  if (menu) {
    menu.open = false;
    return true;
  }
  return false;
}

/**
 * Act on one back press.
 *
 * @param event - from the App plugin.
 * @param doc - the document.
 * @param goBack - goes back in history.
 */
export function handleBack(
  event: BackButtonListenerEvent,
  doc: Document = document,
  goBack: () => void = () => window.history.back()
): void {
  if (closeOverlay(doc)) return;
  if (event.canGoBack) {
    goBack();
  } else {
    void App.minimizeApp();
  }
}

/** Listen for back presses (Android only; iOS never fires the event). */
export function installBackButton(): void {
  void App.addListener("backButton", (event) => handleBack(event));
}
