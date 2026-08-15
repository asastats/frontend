/**
 * @file Framework-free notification seam.
 *
 * The package used to call `M.toast` directly, which meant every host page had
 * to be a Materialize page. It now dispatches a cancelable DOM event and lets
 * the host decide how a message is rendered:
 *
 * * a host that renders the message calls `preventDefault()` to claim it;
 * * with no listener the event goes uncancelled and we append a plain node
 *   carrying `data-notice`, which any stylesheet can target.
 *
 * Nothing here knows about a CSS framework, so the same build works under
 * Materialize today and DaisyUI after the migration.
 */

/** How a message should be read: an error demands attention, info does not. */
export type NoticeLevel = "error" | "info";

/** Event a host listens for to render package messages itself. */
export const NOTIFY_EVENT = "asastats:notify";

/** How long the built-in fallback notice stays on screen. */
export const NOTICE_TIMEOUT_MS = 5000;

/** Payload carried by {@link NOTIFY_EVENT}. */
export interface NotifyDetail {
  /** Human-readable text. Treated as untrusted: hosts must not parse it as markup. */
  message: string;
  /** Severity, for hosts that style by level. */
  level: NoticeLevel;
}

/**
 * Surface a message to the user.
 *
 * @param host - Element the fallback notice is appended to, and the event's
 *   dispatch target so it bubbles through the component's own subtree. Pass
 *   `null` for callers with no container: the event still fires on `document`,
 *   but there is nowhere to place a fallback, so an unhandled message is
 *   dropped rather than appended to the page body.
 * @param message - Text to show. Always rendered via `textContent`.
 * @param level - Severity; defaults to `"error"`, which is what every current
 *   caller reports.
 * @returns Whether a host claimed the message.
 */
export function notify(
  host: HTMLElement | null,
  message: string,
  level: NoticeLevel = "error"
): boolean {
  const detail: NotifyDetail = { message, level };
  const target: EventTarget = host ?? document;
  // dispatchEvent returns false once a listener has called preventDefault().
  const claimed = !target.dispatchEvent(
    new CustomEvent<NotifyDetail>(NOTIFY_EVENT, {
      detail,
      bubbles: true,
      cancelable: true,
    })
  );
  if (claimed || !host) {
    return claimed;
  }

  const notice = document.createElement("div");
  notice.dataset.notice = level;
  // Errors interrupt; info is announced only when the user is idle.
  notice.setAttribute("role", level === "error" ? "alert" : "status");
  notice.textContent = message;
  host.appendChild(notice);
  setTimeout(() => notice.remove(), NOTICE_TIMEOUT_MS);
  return false;
}
