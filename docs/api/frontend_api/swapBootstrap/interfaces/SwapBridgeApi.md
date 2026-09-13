[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBootstrap](../README.md) / SwapBridgeApi

# Interface: SwapBridgeApi

Defined in: [swapBootstrap.ts:51](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L51)

The narrow surface the swap widget (widgets repo) calls via the global.

## Properties

### activeAddress

> **activeAddress**: () => `string` \| `null`

Defined in: [swapBootstrap.ts:53](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L53)

Currently active/connected Algorand address, or null.

#### Returns

`string` \| `null`

***

### assetCreator

> **assetCreator**: (`assetId`) => `Promise`\<`string` \| `null`\>

Defined in: [swapBootstrap.ts:71](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L71)

Creator address of `assetId` read from the chain, or null when it cannot
be read.

Exists for the dust sweep, which gives a holding away by closing it to the
asset's creator. Its browser-side check compared that destination against
an address carried in the same response as the transaction bytes, so a
consistent answer could name anything (audit finding `S2`). This is the
independent source that check needed, and the algod client is already here
for `isOptedIn`.

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`string` \| `null`\>

***

### haystackSigner

> **haystackSigner**: [`HaystackSignerFn`](../type-aliases/HaystackSignerFn.md)

Defined in: [swapBootstrap.ts:77](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L77)

Signer for composer-based routers (Haystack) that pass live Transaction
objects. Pre-encodes each Transaction to bytes before forwarding to
use-wallet's signer, bridging the cross-bundle object/bytes boundary.

***

### optIn

> **optIn**: (`assetId`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:59](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L59)

Opt the active account into `assetId` (pre-flight 0-amount self-transfer).

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`string`\>

***

### signAndSend

> **signAndSend**: (`group`, `opts`) => `Promise`\<`string`\>

Defined in: [swapBootstrap.ts:55](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L55)

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

Defined in: [swapBootstrap.ts:57](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L57)

Sign and submit an engine group with a backend-signed quote transaction.

#### Parameters

##### group

[`PartialSignedGroup`](../../swapBridge/interfaces/PartialSignedGroup.md)

#### Returns

`Promise`\<`string`\>

***

### ~~signer~~

> **signer**: `TransactionSigner`

Defined in: [swapBootstrap.ts:84](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L84)

#### Deprecated

Use haystackSigner for Haystack. Kept for back-compat.
use-wallet's raw TransactionSigner (expects encoded Uint8Array[], not
Transaction objects — will DataView-fail if called with live Transactions
from a foreign bundle).
