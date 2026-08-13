[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / signAndSendPartial

# Function: signAndSendPartial()

> **signAndSendPartial**(`group`, `deps`): `Promise`\<`string`\>

Defined in: [swapBridge.ts:210](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L210)

Sign and submit a group that already contains backend signatures.

The group is already assembled and grouped by the engine. Unlike
`signAndSend`, this function must not prepend opt-ins, clear group IDs or
reassign the group: doing any of those would invalidate the quote-signer's
signature and the signed floor note.

## Parameters

### group

[`PartialSignedGroup`](../interfaces/PartialSignedGroup.md)

### deps

[`SignAndSendDeps`](../interfaces/SignAndSendDeps.md)

## Returns

`Promise`\<`string`\>
