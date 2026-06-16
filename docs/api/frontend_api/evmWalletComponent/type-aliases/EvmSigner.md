[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmWalletComponent](../README.md) / EvmSigner

# Type Alias: EvmSigner

> **EvmSigner** = (`provider`, `address`, `message`) => `Promise`\<`string`\>

Defined in: [evmWalletComponent.ts:50](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L50)

Signs `message` for `address` via `provider`; resolves to a 0x signature.

## Parameters

### provider

[`Eip1193Provider`](../interfaces/Eip1193Provider.md)

### address

`string`

### message

`string`

## Returns

`Promise`\<`string`\>
