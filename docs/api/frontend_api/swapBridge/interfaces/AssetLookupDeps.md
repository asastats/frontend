[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / AssetLookupDeps

# Interface: AssetLookupDeps

Defined in: [swapBridge.ts:376](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L376)

The one algod call [assetCreator](../functions/assetCreator.md) needs, injected so it can be tested.

## Properties

### getAsset

> **getAsset**: (`assetId`) => `Promise`\<`unknown`\>

Defined in: [swapBridge.ts:378](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L378)

Fetch an asset's on-chain parameters (algod `getAssetByID`).

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`unknown`\>
