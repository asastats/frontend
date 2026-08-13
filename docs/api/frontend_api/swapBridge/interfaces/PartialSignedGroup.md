[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / PartialSignedGroup

# Interface: PartialSignedGroup

Defined in: [swapBridge.ts:72](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L72)

A group whose quote authorization was signed by the backend.

## Properties

### quoteSignerIndex

> **quoteSignerIndex**: `number`

Defined in: [swapBridge.ts:78](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L78)

The quote-signer transaction index, required to be the final index.

***

### signedTransactions

> **signedTransactions**: `Record`\<`string`, `Uint8Array`\>

Defined in: [swapBridge.ts:76](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L76)

Signed transaction blobs keyed by their group index.

***

### transactions

> **transactions**: `Uint8Array`\<`ArrayBufferLike`\>[]

Defined in: [swapBridge.ts:74](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L74)

Complete ordered group, encoded without signatures.
