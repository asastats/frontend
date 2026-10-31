/**
 * @file Seeds the index page's checked-address list from the old Flutter app, once.
 *
 * The list itself is `website/static/js/index.js`; its key, cap and patterns must
 * match the ones here (frontend docs/logbook.md).
 */

import { Capacitor, registerPlugin } from "@capacitor/core";

/** mobile/plugins/flutterdata: the entries as Flutter saved them, newest first. */
export interface FlutterDataPlugin {
  readAddresses(): Promise<{ addresses: string[] }>;
}

export const FlutterData = registerPlugin<FlutterDataPlugin>("FlutterData");

export const RECENT_KEY = "asastats.recentAddresses";
/** Set once seeded, so entries forgotten later do not come back. */
export const SEEDED_KEY = "asastats.flutterSeeded";
const RECENT_LIMIT = 20;
const ADDRESS_PATTERN = /^[A-Z2-7]{58}$/;
const NAME_PATTERN = /^[a-z0-9-]+(?:\.[a-z0-9-]+)*\.algo(?:\/(?:ans|nfd))?$/i;

/**
 * Split saved entries (Flutter kept a multi-address search as one string) and keep
 * the addresses and .algo names.
 *
 * @param saved - entries as read.
 * @returns the valid entries, in order.
 */
export function validEntries(saved: unknown[]): string[] {
  return saved
    .filter((entry): entry is string => typeof entry === "string")
    .flatMap((entry) => entry.split(/[\s,]+/))
    .filter((entry) => ADDRESS_PATTERN.test(entry) || NAME_PATTERN.test(entry));
}

/**
 * The app's own entries first (they are newer), then Flutter's; no repeats, capped.
 *
 * @param own - what the list holds now.
 * @param flutter - what the Flutter app saved.
 * @returns the merged list.
 */
export function mergeEntries(own: string[], flutter: string[]): string[] {
  return [...own, ...flutter]
    .filter((entry, position, all) => all.indexOf(entry) === position)
    .slice(0, RECENT_LIMIT);
}

function storedEntries(storage: Storage): string[] {
  try {
    const stored: unknown = JSON.parse(storage.getItem(RECENT_KEY) ?? "[]");
    return Array.isArray(stored) ? validEntries(stored) : [];
  } catch {
    return [];
  }
}

/**
 * Merge the Flutter app's addresses into the list once, if the shell can read them.
 *
 * A shell without the plugin, or a failed read, leaves the flag unset so a later
 * start tries again.
 *
 * @param storage - where the list lives.
 * @returns whether the list was seeded on this call.
 */
export async function seedFlutterAddresses(storage: Storage = window.localStorage): Promise<boolean> {
  try {
    if (storage.getItem(SEEDED_KEY) || !Capacitor.isPluginAvailable("FlutterData")) return false;
    const { addresses } = await FlutterData.readAddresses();
    const flutter = validEntries(Array.isArray(addresses) ? addresses : []);
    if (flutter.length) {
      storage.setItem(RECENT_KEY, JSON.stringify(mergeEntries(storedEntries(storage), flutter)));
    }
    storage.setItem(SEEDED_KEY, "1");
    return true;
  } catch {
    return false;
  }
}

/** Start the one-time seeding without holding up the rest of app.js. */
export function installFlutterAddresses(): void {
  void seedFlutterAddresses();
}
