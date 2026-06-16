import {
  DEFAULT_MANAGE_API_BASE,
  ManageAddressesComponent,
  type ManageDeps,
} from "./manageAddressesComponent";

/**
 * Mount the connected-addresses manager when its container is present.
 *
 * Reads `data-api-base` and `data-wc-project-id` from `#connected-addresses`,
 * then renders and binds a {@link ManageAddressesComponent}. No-ops when the
 * container is absent, so it is safe to call on every page. The browser/wallet
 * adapters are imported lazily and only when no deps are injected, keeping
 * viem/WalletConnect out of the test path.
 *
 * @param deps - Optional injected dependencies (used by tests).
 * @param doc - Document to query (defaults to the global document).
 * @returns The mounted component, or null when no container is present.
 */
export async function initManageAddresses(
  deps: Partial<ManageDeps> = {},
  doc: Document = document
): Promise<ManageAddressesComponent | null> {
  const container = doc.querySelector<HTMLElement>("#connected-addresses");
  if (!container) {
    return null;
  }

  const apiBase = container.dataset.apiBase || DEFAULT_MANAGE_API_BASE;

  let stepUpSign = deps.stepUpSign;
  let addAddress = deps.addAddress;
  /* istanbul ignore next -- loads browser/viem adapters on real pages only */
  if (!stepUpSign || !addAddress) {
    const adapters = await import("./manageAdapters");
    const built = adapters.defaultManageDeps({
      apiBase,
      wcProjectId: container.dataset.wcProjectId || "",
      addUrl: container.dataset.addUrl || "",
    });
    stepUpSign = stepUpSign || built.stepUpSign;
    addAddress = addAddress || built.addAddress;
  }

  const component = new ManageAddressesComponent(container, apiBase, {
    stepUpSign,
    addAddress,
    fetchFn: deps.fetchFn,
  });
  await component.bind();
  return component;
}
