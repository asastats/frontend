[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBootstrap](../README.md) / SwapBridgeApi

# Interface: SwapBridgeApi

Defined in: [swapBootstrap.ts:33](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L33)

The narrow surface the swap widget (widgets repo) calls via the global.

## Properties

### activeAddress

> **activeAddress**: () => `string` \| `null`

Defined in: [swapBootstrap.ts:35](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L35)

Currently active/connected Algorand address, or null.

#### Returns

`string` \| `null`

***

### haystackSigner

> **haystackSigner**: [`HaystackSignerFn`](../type-aliases/HaystackSignerFn.md)

Defined in: [swapBootstrap.ts:47](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L47)

Signer for composer-based routers (Haystack) that pass live Transaction
objects. Pre-encodes each Transaction to bytes before forwarding to
use-wallet's signer, bridging the cross-bundle object/bytes boundary.

***

### optIn

> **optIn**: (`assetId`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:41](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L41)

Opt the active account into `assetId` (pre-flight 0-amount self-transfer).

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`string`\>

***

### signAndSend

> **signAndSend**: (`group`, `opts`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:37](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L37)

Sign + submit + confirm a prepared, grouped, unsigned txn group.

#### Parameters

##### group

`Uint8Array`\<`ArrayBufferLike`\>[]

##### opts

[`SwapOpts`](../../swapBridge/interfaces/SwapOpts.md)

#### Returns

`Promise`\<`string`\>

***

### signAndSendPartial

> **signAndSendPartial**: (`group`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:39](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L39)

Sign and submit an engine group with a backend-signed quote transaction.

#### Parameters

##### group

[`PartialSignedGroup`](../../swapBridge/interfaces/PartialSignedGroup.md)

#### Returns

`Promise`\<`string`\>

***

### ~~signer~~

> **signer**: `TransactionSigner`

Defined in: [swapBootstrap.ts:54](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L54)

#### Deprecated

Use haystackSigner for Haystack. Kept for back-compat.
use-wallet's raw TransactionSigner (expects encoded Uint8Array[], not
Transaction objects — will DataView-fail if called with live Transactions
from a foreign bundle).
