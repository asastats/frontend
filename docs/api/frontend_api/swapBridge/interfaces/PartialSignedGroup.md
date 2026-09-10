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

### reauthorize?

> `optional` **reauthorize?**: (`transactions`, `authorization`) => `Promise`\<`Uint8Array`\<`ArrayBufferLike`\>\>

Defined in: [swapBridge.ts:91](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L91)

Ask the backend to authorise the group the wallet handed back.

Supplied by the widget rather than by the wallet deps because the endpoint
is the widget's: the same place that fetched this group knows where to ask
about it. Omit it and a rewritten group is reported rather than rescued,
which is what every caller did before this existed.

Takes the wallet's signed transactions in group order without the
authorisation, plus the authorisation blob the backend issued, and resolves
with a replacement authorisation signed over the wallet's group.

#### Parameters

##### transactions

`Uint8Array`\<`ArrayBufferLike`\>[]

##### authorization

`Uint8Array`

#### Returns

`Promise`\<`Uint8Array`\<`ArrayBufferLike`\>\>

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
