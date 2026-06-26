[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / optIn

# Function: optIn()

> **optIn**(`assetId`, `deps`): `Promise`\<`string`\>

Defined in: [swapBridge.ts:223](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L223)

Opt the active account into `assetId` as a standalone pre-flight transaction.

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
