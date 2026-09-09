[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletAdapters](../README.md) / getWalletAdapters

# Function: getWalletAdapters()

> **getWalletAdapters**(`descriptors?`): `WalletAdapterConfig`[]

Defined in: walletAdapters.ts:26

Maps an array of backend wallet descriptors or IDs to use-wallet v5 adapter objects.
Unrecognized IDs (e.g. deprecated wallets like Exodus) are safely filtered out.

## Parameters

### descriptors?

(`string` \| \{ `id`: `string`; \})[]

Array of wallet IDs or `{ id: string }` descriptors from the backend.

## Returns

`WalletAdapterConfig`[]

Array of supported v5 wallet adapters.
