/**
 * @file A light tap on copy buttons (`.copy`, bound by site.js) and on anything
 * marked `data-app-haptic`.
 */

import { Haptics, ImpactStyle } from "@capacitor/haptics";

/**
 * Tap lightly when a click lands on a copy button or `data-app-haptic` element.
 *
 * @param doc - the document to listen on.
 */
export function installHaptics(doc: Document = document): void {
  doc.addEventListener("click", (event) => {
    if ((event.target as Element | null)?.closest?.(".copy, [data-app-haptic]")) {
      void Haptics.impact({ style: ImpactStyle.Light });
    }
  });
}
