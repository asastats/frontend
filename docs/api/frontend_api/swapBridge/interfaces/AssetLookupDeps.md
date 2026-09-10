[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / AssetLookupDeps

# Interface: AssetLookupDeps

Defined in: [swapBridge.ts:616](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L616)

The one algod call [assetCreator](../functions/assetCreator.md) needs, injected so it can be tested.

## Properties

### getAsset

> **getAsset**: (`assetId`) => `Promise`\<`unknown`\>

Defined in: [swapBridge.ts:618](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L618)

Fetch an asset's on-chain parameters (algod `getAssetByID`).

#### Parameters

##### assetId

`number`

#### Returns

`Promise`\<`unknown`\>
