[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / AssetLookupDeps

# Interface: AssetLookupDeps

Defined in: [swapBridge.ts:288](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L288)

The one algod call [assetCreator](../functions/assetCreator.md) needs, injected so it can be tested.

## Properties

### getAsset

> **getAsset**: (`assetId`) => `Promise`\<`unknown`\>

Defined in: [swapBridge.ts:290](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L290)

Fetch an asset's on-chain parameters (algod `getAssetByID`).

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`unknown`\>
