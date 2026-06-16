[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [evmWalletComponent](../README.md) / EvmSigner

# Type Alias: EvmSigner

> **EvmSigner** = (`provider`, `address`, `message`) => `Promise`\<`string`\>

Defined in: evmWalletComponent.ts:50

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
