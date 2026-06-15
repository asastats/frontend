import {
  DEFAULT_EVM_API_BASE,
  EvmWalletComponent,
  type EvmConnector,
  type EvmSigner,
} from "./EvmWalletComponent";

/** Injectable factories so the bootstrap can be tested without viem/WalletConnect. */
export interface EvmBootstrapDeps {
  /** Builds the connector list for a given WalletConnect project id. */
  connectorFactory: (projectId: string) => EvmConnector[] | Promise<EvmConnector[]>;
  /** Signs the challenge message. */
  signer: EvmSigner;
}

/**
 * Mount the EVM wallet UI when its container is present.
 *
 * Reads `data-api-base` (login vs link mount point) and `data-wc-project-id`
 * (empty disables WalletConnect, leaving injected wallets only) from
 * `#evm-wallet-connect`, then renders and binds an {@link EvmWalletComponent}.
 * No-ops when the container is absent, so it is safe to call on every page.
 *
 * The real browser/viem adapters are imported lazily and only when no deps are
 * injected, keeping those libraries out of the test path.
 *
 * @param deps - Optional injected factories (used by tests).
 * @param doc - Document to query (defaults to the global document).
 * @returns The mounted component, or null when no container is present.
 */
export async function initEvm(
  deps: Partial<EvmBootstrapDeps> = {},
  doc: Document = document
): Promise<EvmWalletComponent | null> {
  /** Container that gates EVM initialization and carries configuration. */
  const container = doc.querySelector<HTMLElement>("#evm-wallet-connect");
  if (!container) {
    return null;
  }

  /** Login or link mount point of the EVM API. */
  const apiBase = container.dataset.apiBase || DEFAULT_EVM_API_BASE;
  /** WalletConnect project id; empty string means injected-only. */
  const projectId = container.dataset.wcProjectId || "";

  let connectorFactory = deps.connectorFactory;
  let signer = deps.signer;
  /* istanbul ignore next -- loads browser/viem adapters on real pages only */
  if (!connectorFactory || !signer) {
    const adapters = await import("./evmConnectors");
    connectorFactory = connectorFactory || adapters.getDefaultConnectors;
    signer = signer || adapters.defaultEvmSigner;
  }

  const component = new EvmWalletComponent(container, apiBase, {
    listConnectors: () => connectorFactory!(projectId),
    sign: signer!,
  });
  await component.bind();
  return component;
}
