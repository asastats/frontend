[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResumeEvm](../README.md) / takeEvmStep

# Function: takeEvmStep()

> **takeEvmStep**(`storage`, `href`, `now`): [`EvmStep`](../type-aliases/EvmStep.md) \| `null`

Defined in: [walletResumeEvm.ts:129](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L129)

Take this page's pending EVM step out of storage (before any network call).

A fresh step for another page is left for that page until it expires.

## Parameters

### storage

`Storage`

localStorage.

### href

`string`

this page.

### now

`number`

the time, in ms.

## Returns

[`EvmStep`](../type-aliases/EvmStep.md) \| `null`

a well-formed step (V6), or null.
