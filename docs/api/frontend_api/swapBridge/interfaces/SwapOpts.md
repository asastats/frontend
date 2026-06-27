[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / SwapOpts

# Interface: SwapOpts

Defined in: [swapBridge.ts:27](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L27)

Options passed from the controller with each swap call.

## Properties

### outputAssetId

> **outputAssetId**: `number`

Defined in: [swapBridge.ts:29](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L29)

The output asset id for this swap.

***

### referrer?

> `optional` **referrer?**: `string`

Defined in: [swapBridge.ts:33](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L33)

Referrer address; omit or pass "" for no referrer leg.

***

### userNeedsOptIn

> **userNeedsOptIn**: `boolean`

Defined in: [swapBridge.ts:31](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L31)

Whether the user still needs to opt into the output asset.
