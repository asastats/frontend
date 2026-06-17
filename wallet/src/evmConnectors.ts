/* istanbul ignore file -- browser/wallet adapters; not exercisable headless */
import type {
  Eip1193Provider,
  EvmConnector,
  EvmSigner,
} from "./evmWalletComponent";

/**
 * Browser-only adapters that produce concrete {@link EvmConnector}s and an
 * {@link EvmSigner}. These touch wallet globals, the EIP-6963 event protocol,
 * WalletConnect and viem, none of which run under jsdom, so the file is
 * excluded from coverage. The testable orchestration lives in
 * `EvmWalletComponent.ts`, which depends only on the injected shapes.
 */

/** Provider detail announced over the EIP-6963 discovery protocol. */
interface Eip6963ProviderDetail {
  info: { uuid: string; name: string; icon: string; rdns: string };
  provider: Eip1193Provider;
}

/**
 * Discover injected EVM wallets via EIP-6963. Dispatches the request event and
 * collects announcements for a short window, returning one connector per wallet.
 *
 * @param timeoutMs - Collection window for announcements.
 * @returns Connectors for every announced injected wallet.
 */
export function discoverInjectedConnectors(
  timeoutMs = 300
): Promise<EvmConnector[]> {
  return new Promise((resolve) => {
    const details: Eip6963ProviderDetail[] = [];
    const onAnnounce = (event: Event) => {
      const detail = (event as CustomEvent).detail as Eip6963ProviderDetail;
      if (
        detail?.info?.uuid &&
        !details.some((d) => d.info.uuid === detail.info.uuid)
      ) {
        details.push(detail);
      }
    };
    window.addEventListener("eip6963:announceProvider", onAnnounce);
    window.dispatchEvent(new Event("eip6963:requestProvider"));
    setTimeout(() => {
      window.removeEventListener("eip6963:announceProvider", onAnnounce);
      resolve(
        details.map((d) => ({
          id: d.info.rdns,
          name: d.info.name,
          icon: d.info.icon,
          connect: async () => {
            const accounts = (await d.provider.request({
              method: "eth_requestAccounts",
            })) as string[];
            return { provider: d.provider, address: accounts?.[0] ?? "" };
          },
        }))
      );
    }, timeoutMs);
  });
}

/**
 * Build a WalletConnect connector. The provider library is imported lazily so
 * the dependency only loads when a project id is configured and the user picks
 * WalletConnect.
 *
 * @param projectId - Reown/WalletConnect Cloud project id.
 * @returns A connector that opens the WalletConnect modal.
 */
export function walletConnectConnector(projectId: string): EvmConnector {
  return {
    id: "walletconnect",
    name: "WalletConnect",
    connect: async () => {
      const { EthereumProvider } = await import(
        "@walletconnect/ethereum-provider"
      );
      const provider = await EthereumProvider.init({
        projectId,
        chains: [1],
        optionalChains: [1],
        showQrModal: true,
      });
      await provider.connect();
      const accounts = (await provider.request({
        method: "eth_accounts",
      })) as string[];
      return {
        provider: provider as unknown as Eip1193Provider,
        address: accounts?.[0] ?? "",
      };
    },
  };
}

/**
 * Default connector set: injected wallets discovered via EIP-6963, plus a
 * WalletConnect option when a project id is configured.
 *
 * @param projectId - WalletConnect project id (empty disables WalletConnect).
 * @returns The connectors to offer the user.
 */
export async function getDefaultConnectors(
  projectId: string
): Promise<EvmConnector[]> {
  const injected = await discoverInjectedConnectors();
  return projectId
    ? [...injected, walletConnectConnector(projectId)]
    : injected;
}

/**
 * Default signer: EIP-191 `personal_sign` of the challenge via viem, imported
 * lazily so viem only loads when a signature is actually requested.
 */
export const defaultEvmSigner: EvmSigner = async (provider, address, message) => {
  const { createWalletClient, custom } = await import("viem");
  const client = createWalletClient({ transport: custom(provider as any) });
  return client.signMessage({ account: address as `0x${string}`, message });
};
