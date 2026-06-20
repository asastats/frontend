[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBootstrap](../README.md) / SwapBridgeApi

# Interface: SwapBridgeApi

Defined in: [swapBootstrap.ts:14](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L14)

The narrow surface the swap widget (widgets repo) calls via the global.

## Properties

### activeAddress

> **activeAddress**: () => `string` \| `null`

Defined in: [swapBootstrap.ts:16](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L16)

Currently active/connected Algorand address, or null.

#### Returns

`string` \| `null`

***

### optIn

> **optIn**: (`assetId`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:20](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L20)

Opt the active account into `assetId` (pre-flight 0-amount self-transfer).

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`string`\>

***

### signAndSend

> **signAndSend**: (`group`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:18](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L18)

Sign + submit + confirm a prepared, grouped, unsigned txn group.

#### Parameters

##### group

`Uint8Array`\<`ArrayBufferLike`\>[]

#### Returns

`Promise`\<`string`\>
