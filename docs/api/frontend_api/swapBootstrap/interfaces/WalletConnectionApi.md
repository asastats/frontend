[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [swapBootstrap](../README.md) / WalletConnectionApi

# Interface: WalletConnectionApi

Defined in: [swapBootstrap.ts:97](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L97)

Which Algorand account this browser has connected -- and nothing else.

**Published separately from [SwapBridgeApi](SwapBridgeApi.md) on purpose.** Connection
state is a fact about the browser that several features need and none of them
owns. It used to be readable only off `window.asastatsSwap`, so the dust
sweep -- which needs a connected wallet and no part of the swap -- could only
learn it by asking the swap. Any swap-side failure then removed a feature
that does not depend on the swap, and one did: see the note on `signer`.

## Properties

### activeAddress

> **activeAddress**: () => `string` \| `null`

Defined in: [swapBootstrap.ts:99](https://github.com/asastats/frontend/blob/main/wallet/src/swapBootstrap.ts#L99)

Currently active/connected Algorand address, or null.

#### Returns

`string` \| `null`
