[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / signStep

# Function: signStep()

> **signStep**(`fields`, `now?`): (`session`) => [`SignStep`](../interfaces/SignStep.md) \| `null`

Defined in: [walletResume.ts:204](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L204)

The step for a sign-in proof in progress.

## Parameters

### fields

`Pick`\<[`SignStep`](../interfaces/SignStep.md), `"wallet"` \| `"url"` \| `"address"` \| `"nonce"` \| `"note"` \| `"apiBase"` \| `"next"` \| `"binding"`\>

what the verify call will need.

### now?

() => `number`

the time, in ms.

## Returns

a function for [watchStep](watchStep.md).

(`session`) => [`SignStep`](../interfaces/SignStep.md) \| `null`
