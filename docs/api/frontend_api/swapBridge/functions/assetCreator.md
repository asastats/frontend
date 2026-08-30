[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / assetCreator

# Function: assetCreator()

> **assetCreator**(`assetId`, `deps`): `Promise`\<`string` \| `null`\>

Defined in: [swapBridge.ts:314](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L314)

Return the on-chain creator of `assetId`, or null when it cannot be read.

**This is a security control's only source of truth, not a convenience.**
The dust sweep gives a holding away by closing it to the asset's creator,
and its browser-side check used to compare that destination against an
address carried in the same response as the transaction bytes — so a
response that agreed with itself could name anything (audit finding `S2`).
This is the second opinion that check needs, and it lives here rather than
in `swapBootstrap` because that module is `istanbul ignore file`d as
untestable glue. Deciding a forfeit is not glue.

**Null on every failure, deliberately.** The caller refuses a forfeit it
cannot confirm, so a thrown request, an asset that does not exist and a
response missing `params` must all reach it the same way. Returning null
rather than rethrowing keeps that decision in one place.

## Parameters

### assetId

`number`

The asset whose creator to read.

### deps

[`AssetLookupDeps`](../interfaces/AssetLookupDeps.md)

Injected algod lookup.

## Returns

`Promise`\<`string` \| `null`\>

The creator address, or null when it could not be determined.
