[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / OptInDeps

# Interface: OptInDeps

Defined in: [swapBridge.ts:211](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L211)

Extra collaborator for [optIn](../functions/optIn.md): build the (impure) opt-in transaction.

## Extends

- [`SignAndSendDeps`](SignAndSendDeps.md)

## Properties

### activeAddress

> **activeAddress**: () => `string` \| `null`

Defined in: [swapBridge.ts:43](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L43)

Currently active/connected Algorand address, or null when none.

#### Returns

`string` \| `null`

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`activeAddress`](SignAndSendDeps.md#activeaddress)

***

### availableMicroAlgos

> **availableMicroAlgos**: (`addr`) => `Promise`\<`bigint`\>

Defined in: [swapBridge.ts:67](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L67)

Return the number of microAlgos the `addr` can spend without dipping
below its min-balance (amount − min-balance).

#### Parameters

##### addr

`string`

#### Returns

`Promise`\<`bigint`\>

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`availableMicroAlgos`](SignAndSendDeps.md#availablemicroalgos)

***

### buildOptIn

> **buildOptIn**: (`assetId`) => `Promise`\<`Uint8Array`\<`ArrayBufferLike`\>[]\>

Defined in: [swapBridge.ts:213](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L213)

Build the encoded, unsigned 0-amount self asset-transfer that opts in.

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`Uint8Array`\<`ArrayBufferLike`\>[]\>

***

### isOptedIn

> **isOptedIn**: (`addr`, `assetId`) => `Promise`\<`boolean`\>

Defined in: [swapBridge.ts:62](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L62)

Return whether `addr` is already opted into `assetId`.
(algod accountAssetInformation — 404 means not opted in.)

#### Parameters

##### addr

`string`

##### assetId

`number`

#### Returns

`Promise`\<`boolean`\>

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`isOptedIn`](SignAndSendDeps.md#isoptedin)

***

### signTransactions

> **signTransactions**: (`txns`, `indexesToSign`) => `Promise`\<(`Uint8Array`\<`ArrayBufferLike`\> \| `null`)[]\>

Defined in: [swapBridge.ts:52](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L52)

Sign the encoded, grouped, unsigned transactions with the active wallet.

Must receive ALL transactions in the group (so Pera/wallets can verify
group integrity), with `indexesToSign` indicating which positions the
wallet should actually sign. Returns one blob per entry in `indexesToSign`;
a null entry marks a transaction the wallet declined to sign.

#### Parameters

##### txns

`Uint8Array`\<`ArrayBufferLike`\>[]

##### indexesToSign

`number`[]

#### Returns

`Promise`\<(`Uint8Array`\<`ArrayBufferLike`\> \| `null`)[]\>

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`signTransactions`](SignAndSendDeps.md#signtransactions)

***

### submit

> **submit**: (`signed`) => `Promise`\<`string`\>

Defined in: [swapBridge.ts:69](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L69)

Submit the signed transaction blobs; resolves with the submitted txid.

#### Parameters

##### signed

`Uint8Array`\<`ArrayBufferLike`\>[]

#### Returns

`Promise`\<`string`\>

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`submit`](SignAndSendDeps.md#submit)

***

### suggestedParams

> **suggestedParams**: () => `Promise`\<`any`\>

Defined in: [swapBridge.ts:57](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L57)

Fetch current suggested transaction params from algod.

#### Returns

`Promise`\<`any`\>

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`suggestedParams`](SignAndSendDeps.md#suggestedparams)

***

### waitForConfirmation

> **waitForConfirmation**: (`txid`) => `Promise`\<`void`\>

Defined in: [swapBridge.ts:71](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L71)

Resolve once `txid` is confirmed on-chain (or reject on failure/timeout).

#### Parameters

##### txid

`string`

#### Returns

`Promise`\<`void`\>

#### Inherited from

[`SignAndSendDeps`](SignAndSendDeps.md).[`waitForConfirmation`](SignAndSendDeps.md#waitforconfirmation)
