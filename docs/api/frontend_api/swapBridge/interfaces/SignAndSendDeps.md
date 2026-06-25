[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / SignAndSendDeps

# Interface: SignAndSendDeps

Defined in: [swapBridge.ts:40](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L40)

Injected collaborators for [signAndSend](../functions/signAndSend.md) (all wallet/algod concerns isolated).

## Extended by

- [`OptInDeps`](OptInDeps.md)

## Properties

### activeAddress

> **activeAddress**: () => `string` \| `null`

Defined in: [swapBridge.ts:42](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L42)

Currently active/connected Algorand address, or null when none.

#### Returns

`string` \| `null`

***

### availableMicroAlgos

> **availableMicroAlgos**: (`addr`) => `Promise`\<`bigint`\>

Defined in: [swapBridge.ts:60](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L60)

Return the number of microAlgos the `addr` can spend without dipping
below its min-balance (amount − min-balance).

#### Parameters

##### addr

`string`

#### Returns

`Promise`\<`bigint`\>

***

### isOptedIn

> **isOptedIn**: (`addr`, `assetId`) => `Promise`\<`boolean`\>

Defined in: [swapBridge.ts:55](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L55)

Return whether `addr` is already opted into `assetId`.
(algod accountAssetInformation — 404 means not opted in.)

#### Parameters

##### addr

`string`

##### assetId

`number`

#### Returns

`Promise`\<`boolean`\>

***

### signTransactions

> **signTransactions**: (`txns`) => `Promise`\<(`Uint8Array`\<`ArrayBufferLike`\> \| `null`)[]\>

Defined in: [swapBridge.ts:48](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L48)

Sign the encoded, grouped, unsigned transactions with the active wallet.
Accepts only the indexes the wallet should sign; returns one blob per
input position. A null entry marks a transaction the wallet did not sign.

#### Parameters

##### txns

`Uint8Array`\<`ArrayBufferLike`\>[]

#### Returns

`Promise`\<(`Uint8Array`\<`ArrayBufferLike`\> \| `null`)[]\>

***

### submit

> **submit**: (`signed`) => `Promise`\<`string`\>

Defined in: [swapBridge.ts:62](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L62)

Submit the signed transaction blobs; resolves with the submitted txid.

#### Parameters

##### signed

`Uint8Array`\<`ArrayBufferLike`\>[]

#### Returns

`Promise`\<`string`\>

***

### suggestedParams

> **suggestedParams**: () => `Promise`\<`any`\>

Defined in: [swapBridge.ts:50](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L50)

Fetch current suggested transaction params from algod.

#### Returns

`Promise`\<`any`\>

***

### waitForConfirmation

> **waitForConfirmation**: (`txid`) => `Promise`\<`void`\>

Defined in: [swapBridge.ts:64](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L64)

Resolve once `txid` is confirmed on-chain (or reject on failure/timeout).

#### Parameters

##### txid

`string`

#### Returns

`Promise`\<`void`\>
