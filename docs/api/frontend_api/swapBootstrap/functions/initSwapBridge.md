[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBootstrap](../README.md) / initSwapBridge

# Function: initSwapBridge()

> **initSwapBridge**(`doc?`): `Promise`\<`void`\>

Defined in: [swapBootstrap.ts:242](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L242)

Publish wallet connection state, and the swap bridge when a swap is present.

**Two halves, deliberately, and the smaller one comes first.**

`window.asastatsWallet` is which account this browser has connected. It is
published **first, and outside the `try`** below, so that a signing bridge
which cannot be built cannot take it away. `asastats:wallet-ready` announces
it.

`window.asastatsSwap` is the signing bridge, published for every entry in
`WALLET_ENTRIES` -- the sweep signs through it too.

**Why the first half exists at all.** Deciding whether to *offer* a feature
is not the same question as being able to *sign*, and only the sweep asks the
first one: it reveals its button for a connected account. Reading that off
the signing bridge meant the button vanished whenever the bridge did -- once
because building it threw (see the note on `signer`), once because the page
had no entry to mount it at all. Connection state is a fact about the browser
that no feature owns, so it is published as one.

Safe to call repeatedly: htmx delivers `#id-swap-enabled` after
DOMContentLoaded, so `main.ts` retries on every settle, and this returns at
once once both are up.

## Parameters

### doc?

`Document` = `document`

## Returns

`Promise`\<`void`\>
