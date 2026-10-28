/**
 * Entry for the ASA Stats app (`js/app.js`). base.html loads it only in app
 * mode, after bundle.js.
 */

import { Capacitor } from "@capacitor/core";

import { installAppLock } from "./appLock";
import { installBackButton } from "./backButton";
import { installDeepLinks } from "./deepLinks";
import { download, installDownloads } from "./downloads";
import { installHaptics } from "./haptics";
import { installLinks } from "./links";
import { installResume } from "./resume";
import { installReturn } from "./returnPage";
import { checkPush, disablePush, enablePush, installPush, type DeviceUrls, type PushResult } from "./push";
import { installSignIn, signIn } from "./signIn";
import { installSplash } from "./splash";
import { installStatusBar } from "./statusBar";
import { installHandoff } from "./walletHandoff";

/** The global page scripts feature-detect; see capacitor/HANDOFF.md §6. */
export interface ASAStatsAppApi {
  isApp: true;
  /** Fetch a same-site file and open the share sheet for it. */
  download: (url: string) => Promise<boolean>;
  /** Ask permission and register this device for alerts (widgets `alerts.js`). */
  enablePush: (urls: DeviceUrls) => Promise<PushResult>;
  /** Re-register without prompting; whether this device is on. */
  checkPush: (urls: DeviceUrls) => Promise<boolean>;
  /** Unregister this device; done before logout. */
  disablePush: () => Promise<void>;
  /** Social sign-in through the system browser (F4); whether it was sent. */
  signIn: (provider: string, next?: string) => Promise<boolean>;
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
    target.ASAStatsApp = {
      isApp: true,
      download: (url) => download(url),
      enablePush,
      checkPush,
      disablePush,
      signIn: (provider, next) => signIn(provider, next),
    };
  }
  return target.ASAStatsApp;
}

/**
 * Wire every native behaviour, if the native bridge is present.
 *
 * The user-agent token alone put this page in app mode; without the bridge
 * (an old shell, a browser faking the token) the plugins would only reject.
 *
 * @returns whether the bridge was found.
 */
export function start(): boolean {
  install();
  if (!Capacitor.isNativePlatform()) return false;
  // Before installReturn: a lost wallet step's page wins.
  installHandoff();
  installReturn();
  installSplash();
  installLinks();
  installDownloads();
  installBackButton();
  installDeepLinks();
  installStatusBar();
  installHaptics();
  installPush();
  installSignIn();
  installResume();
  installAppLock();
  return true;
}

start();
