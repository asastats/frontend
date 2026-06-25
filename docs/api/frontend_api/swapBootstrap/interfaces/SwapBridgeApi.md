[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBootstrap](../README.md) / SwapBridgeApi

# Interface: SwapBridgeApi

Defined in: [swapBootstrap.ts:26](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L26)

The narrow surface the swap widget (widgets repo) calls via the global.

## Properties

### activeAddress

> **activeAddress**: () => `string` \| `null`

Defined in: [swapBootstrap.ts:28](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L28)

Currently active/connected Algorand address, or null.

#### Returns

`string` \| `null`

***

### haystackSigner

> **haystackSigner**: [`HaystackSignerFn`](../type-aliases/HaystackSignerFn.md)

Defined in: [swapBootstrap.ts:38](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L38)

Signer for composer-based routers (Haystack) that pass live Transaction
objects. Pre-encodes each Transaction to bytes before forwarding to
use-wallet's signer, bridging the cross-bundle object/bytes boundary.

***

### optIn

> **optIn**: (`assetId`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:32](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L32)

Opt the active account into `assetId` (pre-flight 0-amount self-transfer).

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`string`\>

***

### signAndSend

> **signAndSend**: (`group`, `opts`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:30](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L30)

Sign + submit + confirm a prepared, grouped, unsigned txn group.

#### Parameters

##### group

`Uint8Array`\<`ArrayBufferLike`\>[]

##### opts

[`SwapOpts`](../../swapBridge/interfaces/SwapOpts.md)

#### Returns

`Promise`\<`string`\>

***

### ~~signer~~

> **signer**: `TransactionSigner`

Defined in: [swapBootstrap.ts:45](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L45)

#### Deprecated

Use haystackSigner for Haystack. Kept for back-compat.
use-wallet's raw TransactionSigner (expects encoded Uint8Array[], not
Transaction objects — will DataView-fail if called with live Transactions
from a foreign bundle).
