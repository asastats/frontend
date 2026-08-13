[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / SwapOpts

# Interface: SwapOpts

Defined in: [swapBridge.ts:28](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L28)

Options passed from the controller with each swap call.

## Properties

### outputAssetId

> **outputAssetId**: `number`

Defined in: [swapBridge.ts:30](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L30)

The output asset id for this swap.

***

### referrer?

> `optional` **referrer?**: `string`

Defined in: [swapBridge.ts:34](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L34)

Referrer address; omit or pass "" for no referrer leg.

***

### userNeedsOptIn

> **userNeedsOptIn**: `boolean`

Defined in: [swapBridge.ts:32](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L32)

Whether the user still needs to opt into the output asset.
