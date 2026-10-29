[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / takeStep

# Function: takeStep()

> **takeStep**(`storage`, `href`, `now`): [`Step`](../type-aliases/Step.md) \| `null`

Defined in: [walletResume.ts:234](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L234)

Take this page's pending step out of storage (R4: before any network call).

A step for another page is left for that page until it expires.

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

[`Step`](../type-aliases/Step.md) \| `null`

a well-formed, allowed step, or null.
