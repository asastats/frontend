[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / SignAndSendDeps

# Interface: SignAndSendDeps

Defined in: [swapBridge.ts:19](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L19)

Injected collaborators for [signAndSend](../functions/signAndSend.md) (all wallet/algod concerns isolated).

## Extended by

- [`OptInDeps`](OptInDeps.md)

## Properties

### activeAddress

> **activeAddress**: () => `string` \| `null`

Defined in: [swapBridge.ts:21](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L21)

Currently active/connected Algorand address, or null when none.

#### Returns

`string` \| `null`

***

### signTransactions

> **signTransactions**: (`txns`) => `Promise`\<(`Uint8Array`\<`ArrayBufferLike`\> \| `null`)[]\>

Defined in: [swapBridge.ts:27](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L27)

Sign the encoded, grouped, unsigned transactions with the active wallet.
Returns one entry per input position; a null entry marks a transaction the
wallet did not sign (use-wallet's contract).

#### Parameters

##### txns

`Uint8Array`\<`ArrayBufferLike`\>[]

#### Returns

`Promise`\<(`Uint8Array`\<`ArrayBufferLike`\> \| `null`)[]\>

***

### submit

> **submit**: (`signed`) => `Promise`\<`string`\>

Defined in: [swapBridge.ts:29](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L29)

Submit the signed transaction blobs; resolves with the submitted txid.

#### Parameters

##### signed

`Uint8Array`\<`ArrayBufferLike`\>[]

#### Returns

`Promise`\<`string`\>

***

### waitForConfirmation

> **waitForConfirmation**: (`txid`) => `Promise`\<`void`\>

Defined in: [swapBridge.ts:31](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L31)

Resolve once `txid` is confirmed on-chain (or reject on failure/timeout).

#### Parameters

##### txid

`string`

#### Returns

`Promise`\<`void`\>
