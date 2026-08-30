import { buildStepUpSign } from "./manageAdapters";
import { notify } from "./notify";
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
  // No container to fall back into here, so an unhandled message is dropped --
  // which is exactly what happened before, on any page without Materialize.
  notify(null, message);
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

  // The address list used to need re-initialising here after every htmx swap,
  // because Materialize's collapsible was JS-driven. It is a <details> now, so
  // a freshly swapped list works on arrival and there is nothing to re-bind.
  //
  // Server-signalled failures arrive as an HX-Trigger "wallet-error" event.
  doc.body.addEventListener("wallet-error", (event: Event) => {
    const detail = (event as CustomEvent).detail;
    toast(detail?.value || (typeof detail === "string" ? detail : "Operation failed"));
  });
}
