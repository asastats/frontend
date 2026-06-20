[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / signAndSend

# Function: signAndSend()

> **signAndSend**(`group`, `deps`): `Promise`\<`string`\>

Defined in: [swapBridge.ts:49](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L49)

Sign, submit and confirm a prepared swap transaction group.

Pure orchestration: guards the preconditions, then drives
sign → submit → confirm through the injected collaborators in order. Throws
(and submits nothing) when the group is empty, no wallet account is active, or
the wallet does not return a signature for every transaction in the group. The
"every transaction signed" check assumes a single-signer group (the user's
account signs the input transfer, the router app call(s) and the fee txn); if
a future router needs a foreign- or logicsig-signed leg, relax this here.

## Parameters

### group

`Uint8Array`\<`ArrayBufferLike`\>[]

Encoded, grouped, unsigned transactions ready to sign.

### deps

[`SignAndSendDeps`](../interfaces/SignAndSendDeps.md)

Injected wallet/algod collaborators.

## Returns

`Promise`\<`string`\>

The confirmed transaction id.
