import {
  WalletManager,
  NetworkId,
  type WalletAdapterConfig,
} from "@txnlab/use-wallet";
import { pera } from "@txnlab/use-wallet-pera";
import { defly } from "@txnlab/use-wallet-defly";
import { lute } from "@txnlab/use-wallet-lute";
import { kibisis } from "@txnlab/use-wallet-kibisis";

/** Known v5 adapter factory functions mapped by lowercase wallet ID. */
export const ADAPTER_FACTORIES: Record<string, () => WalletAdapterConfig> = {
  pera: () => pera(),
  defly: () => defly(),
  lute: () => lute(),
  kibisis: () => kibisis(),
};

/**
 * Maps an array of backend wallet descriptors or IDs to use-wallet v5 adapter objects.
 * Unrecognized IDs (e.g. deprecated wallets like Exodus) are safely filtered out.
 *
 * @param descriptors - Array of wallet IDs or `{ id: string }` descriptors from the backend.
 * @returns Array of supported v5 wallet adapters.
 */
export function getWalletAdapters(
  descriptors?: Array<string | { id: string }>
): WalletAdapterConfig[] {
  if (!descriptors || descriptors.length === 0) {
    return [pera(), defly(), lute(), kibisis()];
  }
  const adapters: WalletAdapterConfig[] = [];
  for (const item of descriptors) {
    const id = typeof item === "string" ? item : item?.id;
    if (!id) continue;
    const factory = ADAPTER_FACTORIES[id.toLowerCase()];
    if (factory) {
      adapters.push(factory());
    }
  }
  return adapters.length > 0 ? adapters : [pera(), defly(), lute(), kibisis()];
}

/**
 * Creates a WalletManager instance configured with adapters matching the given IDs.
 *
 * @param descriptors - Array of wallet IDs or `{ id: string }` descriptors.
 * @param network - Network id; mainnet unless a page asks otherwise (the DAO panel on testnet).
 * @returns Configured WalletManager instance.
 */
export function createWalletManager(
  descriptors?: Array<string | { id: string }>,
  network: string = NetworkId.MAINNET
): WalletManager {
  return new WalletManager({
    wallets: withChainId(getWalletAdapters(descriptors), network),
    defaultNetwork: network,
  });
}

/** WalletConnect chain ids of the non-mainnet networks; mainnet keeps the adapters' default. */
export const CHAIN_IDS: Record<string, 416002 | 416003> = { testnet: 416002, betanet: 416003 };

/**
 * Asks Pera and Defly for `network`'s chain, so their session signs there (logbook, 2026-11-25).
 *
 * @param adapters - Adapter configs from {@link getWalletAdapters}.
 * @param network - Network id.
 * @returns The configs, unchanged on mainnet.
 */
export function withChainId(adapters: WalletAdapterConfig[], network: string): WalletAdapterConfig[] {
  const chainId = CHAIN_IDS[network];
  if (!chainId) {
    return adapters;
  }
  return adapters.map((config) => {
    if (config.id === "pera") return pera({ chainId });
    if (config.id === "defly") return defly({ chainId });
    return config;
  });
}

/**
 * Safely converts a Uint8Array of arbitrary size to a Base64 string
 * without exceeding JavaScript engine call-stack argument limits.
 *
 * @param bytes - The binary data to encode.
 * @returns Standard Base64 string.
 */
export function uint8ArrayToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunkSize = 0x8000; // 32 KB chunk
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}
