/**
 * Entry for the ASA Stats app (`js/app.js`). base.html loads it only in app
 * mode, after bundle.js.
 */

/** The global page scripts feature-detect; see capacitor/HANDOFF.md §6. */
export interface ASAStatsAppApi {
  isApp: true;
}

declare global {
  interface Window {
    ASAStatsApp?: ASAStatsAppApi;
  }
}

/**
 * Publish `window.ASAStatsApp` once.
 *
 * @param target - the window to publish on.
 * @returns the published API.
 */
export function install(target: Window = window): ASAStatsAppApi {
  if (!target.ASAStatsApp) {
    target.ASAStatsApp = { isApp: true };
  }
  return target.ASAStatsApp;
}

install();
