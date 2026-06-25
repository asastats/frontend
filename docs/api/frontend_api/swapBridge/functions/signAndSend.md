[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBridge](../README.md) / signAndSend

# Function: signAndSend()

> **signAndSend**(`group`, `deps`, `opts`): `Promise`\<`string`\>

Defined in: [swapBridge.ts:86](https://github.com/asastats/frontend/blob/main/wallet/src/swapBridge.ts#L86)

Sign, submit and confirm a prepared swap transaction group, prepending any
required opt-in legs (user and/or referrer escrow) as shape B.

Build order:
 1. [optional] user opt-in into the output asset (wallet-signed).
 2. [optional] referrer-escrow opt-in — lsig-signed self-transfer when the
    escrow can self-fund its MBR, or the SDK's two-txn pair (user funds the
    MBR, then the lsig opt-in) when it cannot.
 3. The swap txns forwarded from the caller (all wallet-signed).

All entries are cleared of prior group ids and re-assigned a single atomic
group id before signing.

## Parameters

### group

`Uint8Array`\<`ArrayBufferLike`\>[]

Encoded, grouped, unsigned swap transactions from the adapter.

### deps

[`SignAndSendDeps`](../interfaces/SignAndSendDeps.md)

Injected wallet/algod collaborators.

### opts

[`SwapOpts`](../interfaces/SwapOpts.md)

Per-call options: output asset, user opt-in flag, referrer.

## Returns

`Promise`\<`string`\>

The confirmed transaction id (first leg of the submitted group).
