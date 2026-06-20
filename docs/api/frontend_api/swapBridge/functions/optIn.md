[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / optIn

# Function: optIn()

> **optIn**(`assetId`, `deps`): `Promise`\<`string`\>

Defined in: [swapBridge.ts:94](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L94)

Opt the active account into `assetId` as a standalone pre-flight transaction.

The Folks swap group does not opt the user into the output asset (the SDK's
only opt-in helper opts the *router app* in, not the user), and receiving an
ASA you are not opted into fails the whole atomic group. So when holdings show
the target is not yet opted in, the controller calls this first: build a
0-amount self asset-transfer (locking 0.1 ALGO of MBR) and sign + submit +
confirm it through the very same orchestration as a swap. Keeping it a separate
group means Folks' pre-grouped, self-validated transactions are never mutated;
the cost is one extra approval the first time into a new asset, none after.

## Parameters

### assetId

`number`

The output asset to opt into.

### deps

[`OptInDeps`](../interfaces/OptInDeps.md)

Injected collaborators, incl. the impure [OptInDeps.buildOptIn](../interfaces/OptInDeps.md#buildoptin).

## Returns

`Promise`\<`string`\>

The confirmed opt-in transaction id.
