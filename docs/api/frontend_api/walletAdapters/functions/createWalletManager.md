[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletAdapters](../README.md) / createWalletManager

# Function: createWalletManager()

> **createWalletManager**(`descriptors?`): `WalletManager`

Defined in: [walletAdapters.ts:50](https://github.com/asastats/frontend/blob/main/wallet/src/walletAdapters.ts#L50)

Creates a mainnet WalletManager instance configured with adapters matching the given IDs.

## Parameters

### descriptors?

(`string` \| \{ `id`: `string`; \})[]

Array of wallet IDs or `{ id: string }` descriptors.

## Returns

`WalletManager`

Configured WalletManager instance.
