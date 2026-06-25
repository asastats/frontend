[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBootstrap](../README.md) / SwapBridgeApi

# Interface: SwapBridgeApi

Defined in: [swapBootstrap.ts:15](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L15)

The narrow surface the swap widget (widgets repo) calls via the global.

## Properties

### activeAddress

> **activeAddress**: () => `string` \| `null`

Defined in: [swapBootstrap.ts:17](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L17)

Currently active/connected Algorand address, or null.

#### Returns

`string` \| `null`

***

### optIn

> **optIn**: (`assetId`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:21](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L21)

Opt the active account into `assetId` (pre-flight 0-amount self-transfer).

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`string`\>

***

### signAndSend

> **signAndSend**: (`group`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:19](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L19)

Sign + submit + confirm a prepared, grouped, unsigned txn group.

#### Parameters

##### group

`Uint8Array`\<`ArrayBufferLike`\>[]

#### Returns

`Promise`\<`string`\>

***

### signer

> **signer**: `TransactionSigner`

Defined in: [swapBootstrap.ts:23](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L23)

use-wallet signer; used by composer-based routers (Haystack).
