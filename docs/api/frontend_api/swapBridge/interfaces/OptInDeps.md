[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / OptInDeps

# Interface: OptInDeps

Defined in: [swapBridge.ts:73](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L73)

Extra collaborator for [optIn](../functions/optIn.md): build the (impure) opt-in transaction.

## Extends

- [`SignAndSendDeps`](SignAndSendDeps.md)

## Properties

### activeAddress

> **activeAddress**: () => `string` \| `null`

Defined in: [swapBridge.ts:21](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L21)

Currently active/connected Algorand address, or null when none.

#### Returns

`string` \| `null`

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`activeAddress`](SignAndSendDeps.md#activeaddress)

***

### buildOptIn

> **buildOptIn**: (`assetId`) => `Promise`\<`Uint8Array`\<`ArrayBufferLike`\>[]\>

Defined in: [swapBridge.ts:75](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L75)

Build the encoded, unsigned 0-amount self asset-transfer that opts in.

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`Uint8Array`\<`ArrayBufferLike`\>[]\>

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

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`signTransactions`](SignAndSendDeps.md#signtransactions)

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

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`submit`](SignAndSendDeps.md#submit)

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

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`waitForConfirmation`](SignAndSendDeps.md#waitforconfirmation)
