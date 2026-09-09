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
 * Creates a mainnet WalletManager instance configured with adapters matching the given IDs.
 *
 * @param descriptors - Array of wallet IDs or `{ id: string }` descriptors.
 * @returns Configured WalletManager instance.
 */
export function createWalletManager(
  descriptors?: Array<string | { id: string }>
): WalletManager {
  return new WalletManager({
    wallets: getWalletAdapters(descriptors),
    defaultNetwork: NetworkId.MAINNET,
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
