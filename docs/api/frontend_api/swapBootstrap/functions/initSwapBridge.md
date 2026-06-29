[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBootstrap](../README.md) / initSwapBridge

# Function: initSwapBridge()

> **initSwapBridge**(`doc?`): `Promise`\<`void`\>

Defined in: [swapBootstrap.ts:162](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L162)

Wire the swap bridge when a swap widget is present on the page.

No-ops unless a swap entry point is present: the shell accordion container
(`#id-swap-swap`) OR the per-ASA modal marker (`#id-swap-enabled`).
On a swap page it resumes the wallet manager, publishes `window.asastatsSwap`,
then dispatches `asastats:swap-ready` so a widget controller that ran before
the wallet bundle can re-run its render gate.

## Parameters

### doc?

`Document` = `document`

## Returns

`Promise`\<`void`\>
