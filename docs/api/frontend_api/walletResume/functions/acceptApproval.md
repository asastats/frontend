[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / acceptApproval

# Function: acceptApproval()

> **acceptApproval**(`step`): (`message`) => `false` \| \{ `accounts`: `string`[]; `chainId`: `number`; `peerId`: `string`; `peerMeta`: \{ \} \| `null`; \} \| `null`

Defined in: [walletResume.ts:369](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L369)

Accept only the approval of this connect (R2).

## Parameters

### step

[`ConnectStep`](../interfaces/ConnectStep.md)

the connect.

## Returns

the accounts and the wallet's session fields, `false`, or null.

(`message`) => `false` \| \{ `accounts`: `string`[]; `chainId`: `number`; `peerId`: `string`; `peerMeta`: \{ \} \| `null`; \} \| `null`
