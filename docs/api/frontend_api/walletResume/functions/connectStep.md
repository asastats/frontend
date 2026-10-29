[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / connectStep

# Function: connectStep()

> **connectStep**(`wallet`, `url`, `now?`): (`session`) => [`ConnectStep`](../interfaces/ConnectStep.md) \| `null`

Defined in: [walletResume.ts:179](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L179)

The step for a connect in progress.

## Parameters

### wallet

`string`

wallet id.

### url

`string`

this page.

### now?

() => `number`

the time, in ms.

## Returns

a function for [watchStep](watchStep.md).

(`session`) => [`ConnectStep`](../interfaces/ConnectStep.md) \| `null`
