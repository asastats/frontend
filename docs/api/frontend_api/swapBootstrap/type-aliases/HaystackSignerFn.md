[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBootstrap](../README.md) / HaystackSignerFn

# Type Alias: HaystackSignerFn

> **HaystackSignerFn** = (`txnGroup`, `indexesToSign`) => `Promise`\<(`Uint8Array` \| `null`)[]\>

Defined in: [swapBootstrap.ts:20](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L20)

Signer type Haystack's composer calls: Transaction objects + indexes to sign.
Distinct from use-wallet's TransactionSigner which takes encoded Uint8Array[].

## Parameters

### txnGroup

`Transaction`[]

### indexesToSign

`number`[]

## Returns

`Promise`\<(`Uint8Array` \| `null`)[]\>
