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
/** Set once Flutter's bundles are seeded whole; lists seeded before it got them split. */
export const BUNDLES_KEY = "asastats.flutterBundlesSeeded";
const RECENT_LIMIT = 20;
const ADDRESS_PATTERN = /^[A-Z2-7]{58}$/;
const NAME_PATTERN = /^[a-z0-9-]+(?:\.[a-z0-9-]+)*\.algo(?:\/(?:ans|nfd))?$/i;

/**
 * Keep each saved search's addresses and .algo names; a search of several becomes
 * one bundle entry joined by commas, as index.js stores it.
 *
 * @param saved - entries as read.
 * @returns the valid entries, in order.
 */
export function validEntries(saved: unknown[]): string[] {
  return saved
    .filter((entry): entry is string => typeof entry === "string")
    .map((entry) =>
      entry
        .split(/[\s,]+/)
        .filter((part) => ADDRESS_PATTERN.test(part) || NAME_PATTERN.test(part))
        .filter((part, position, all) => all.indexOf(part) === position)
        .join(","),
    )
    .filter((entry) => entry !== "");
}

/** Whether an entry is a bundle of several addresses or names. */
export function isBundle(entry: string): boolean {
  return entry.includes(",");
}

/** The same addresses in any order give the same key (index.js `entryKey`). */
function entryKey(entry: string): string {
  return entry.split(",").sort().join(",");
}

/**
 * The first list's entries first, then the second's; no repeats, capped.
 *
 * @param first - entries that go on top.
 * @param second - entries that follow.
 * @returns the merged list.
 */
export function mergeEntries(first: string[], second: string[]): string[] {
  const all = [...first, ...second];
  const keys = all.map(entryKey);
  return all.filter((_, position) => keys.indexOf(keys[position]) === position).slice(0, RECENT_LIMIT);
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
 * Merge the Flutter app's entries into the list once, if the shell can read them.
 * A list seeded before bundles were kept gets only the bundles, on top
 * (docs/logbook.md).
 *
 * A shell without the plugin, or a failed read, leaves the flags unset so a later
 * start tries again.
 *
 * @param storage - where the list lives.
 * @returns whether the list was seeded on this call.
 */
export async function seedFlutterAddresses(storage: Storage = window.localStorage): Promise<boolean> {
  try {
    if (storage.getItem(BUNDLES_KEY) || !Capacitor.isPluginAvailable("FlutterData")) return false;
    const { addresses } = await FlutterData.readAddresses();
    const flutter = validEntries(Array.isArray(addresses) ? addresses : []);
    const seededBefore = Boolean(storage.getItem(SEEDED_KEY));
    const bundles = flutter.filter(isBundle);
    if (seededBefore ? bundles.length : flutter.length) {
      const own = storedEntries(storage);
      const merged = seededBefore ? mergeEntries(bundles, own) : mergeEntries(own, flutter);
      storage.setItem(RECENT_KEY, JSON.stringify(merged));
    }
    storage.setItem(SEEDED_KEY, "1");
    storage.setItem(BUNDLES_KEY, "1");
    return true;
  } catch {
    return false;
  }
}

/** Start the one-time seeding without holding up the rest of app.js. */
export function installFlutterAddresses(): void {
  void seedFlutterAddresses();
}
