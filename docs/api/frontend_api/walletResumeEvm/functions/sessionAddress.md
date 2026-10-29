[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResumeEvm](../README.md) / sessionAddress

# Function: sessionAddress()

> **sessionAddress**(`session`): `string` \| `null`

Defined in: [walletResumeEvm.ts:159](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L159)

The one EVM address of a session (V2), lower-cased.

## Parameters

### session

[`WcSession`](../interfaces/WcSession.md) \| `undefined`

the restored session.

## Returns

`string` \| `null`

the address, or null unless there is exactly one valid one.
