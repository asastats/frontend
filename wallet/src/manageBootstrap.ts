/* istanbul ignore file -- browser/htmx glue; runStepUp is tested in manageBridge.test */
import { buildStepUpSign } from "./manageAdapters";
import { runStepUp } from "./manageBridge";

const DEFAULT_MANAGE_API_BASE = "/api/v2/wallet";

function getCsrf(doc: Document): string {
  const cookie =
    doc.cookie.match("(^|;)\\s*csrftoken\\s*=\\s*([^;]+)")?.pop() || "";
  return (
    cookie ||
    (doc.querySelector('input[name="csrfmiddlewaretoken"]') as
      | HTMLInputElement
      | null)?.value ||
    ""
  );
}

function toast(message: string): void {
  const M = (window as any).M;
  if (M?.toast) {
    // `text` (not the deprecated `html`) renders as textContent: no markup
    // parsing, so wallet/server-derived strings are surfaced safely.
    M.toast({ text: message, classes: "red darken-1" });
  }
}

function initCollapsible(doc: Document): void {
  const M = (window as any).M;
  const ul = doc.querySelector(".collapsible");
  if (M?.Collapsible?.init && ul) {
    M.Collapsible.init(ul, { accordion: false });
  }
}

/**
 * Wire the connected-addresses manager when its container is present.
 *
 * Plain reducing actions (remove, disable-login) are declarative `hx-post`
 * buttons handled by htmx directly. Privilege-expanding actions carry
 * `data-stepup`; those are intercepted here to obtain a wallet signature before
 * htmx posts the proof. No-ops when the container is absent.
 *
 * @param doc - Document to query (defaults to the global document).
 */
export function initManageAddresses(doc: Document = document): void {
  const container = doc.querySelector<HTMLElement>("#connected-addresses");
  if (!container) {
    return;
  }
  const apiBase = container.dataset.apiBase || DEFAULT_MANAGE_API_BASE;
  const opsUrl = container.dataset.opsUrl || "";
  const stepUpSign = buildStepUpSign({
    apiBase,
    wcProjectId: container.dataset.wcProjectId || "",
  });

  container.addEventListener("click", (event: Event) => {
    const button = (event.target as HTMLElement).closest<HTMLElement>(
      "[data-stepup]"
    );
    if (!button) {
      return; // plain hx-post buttons are handled natively by htmx
    }
    event.preventDefault();
    runStepUp(
      {
        operation: button.dataset.operation || "",
        targetId: Number(button.dataset.targetId),
        enabled: button.dataset.enabled === "true",
      },
      {
        fetchFn: fetch.bind(window),
        csrf: getCsrf(doc),
        apiBase,
        opsUrl,
        stepUpSign,
        ajax: (url, values) => {
          // Resolved per click, not at init: htmx may load after this bundle.
          const htmx = (window as any).htmx;
          if (!htmx?.ajax) {
            return Promise.reject(
              new Error("htmx is not loaded on this page")
            );
          }
          return htmx.ajax("POST", url, {
            target: "#connected-addresses-list",
            swap: "innerHTML",
            source: container,
            values,
          });
        },
      }
    ).catch((error: unknown) =>
      toast(error instanceof Error ? error.message : String(error))
    );
  });

  // Re-init the Materialize collapsible after htmx swaps the list back in.
  doc.body.addEventListener("htmx:afterSwap", (event: Event) => {
    const detail = (event as CustomEvent).detail;
    if (detail?.target?.id === "connected-addresses-list") {
      initCollapsible(doc);
    }
  });
  // Server-signalled failures arrive as an HX-Trigger "wallet-error" event.
  doc.body.addEventListener("wallet-error", (event: Event) => {
    const detail = (event as CustomEvent).detail;
    toast(detail?.value || (typeof detail === "string" ? detail : "Operation failed"));
  });

  initCollapsible(doc);
}
