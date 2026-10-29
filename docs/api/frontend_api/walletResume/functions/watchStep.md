[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / watchStep

# Function: watchStep()

> **watchStep**(`wallet`, `describe`, `target?`): () => `void`

Defined in: [walletResume.ts:143](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L143)

Keep `step` while the wallet is in front; drop it once the page's own flow ends.

Saves on `beforeunload` (fired for the `wc:` hand-off) and when the page is
hidden, reading the session at that moment.

## Parameters

### wallet

the use-wallet wallet being used.

#### id

`string`

### describe

(`session`) => [`Step`](../type-aliases/Step.md) \| `null`

builds the step from the current session, or null.

### target?

`Window` = `window`

the window.

## Returns

a stop function: call it when the flow finished in this page.

() => `void`
