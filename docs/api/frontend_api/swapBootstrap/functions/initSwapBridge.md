[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBootstrap](../README.md) / initSwapBridge

# Function: initSwapBridge()

> **initSwapBridge**(`doc?`): `Promise`\<`void`\>

Defined in: [swapBootstrap.ts:123](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L123)

Wire the swap bridge when a swap widget is present on the page.

No-ops unless the swap container (`#id-folks-swap`, shared by all router
widgets) exists, so it is safe to run everywhere — matching initManageAddresses
/ initEvm. On a swap page it resumes the wallet manager, publishes
`window.asastatsSwap`, then dispatches `asastats:swap-ready` so a widget
controller that ran before the wallet bundle can re-run its render gate.

## Parameters

### doc?

`Document` = `document`

Document to query (defaults to the global document).

## Returns

`Promise`\<`void`\>
