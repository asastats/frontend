[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/walletHandoff](../README.md) / showHandoffNotice

# Function: showHandoffNotice()

> **showHandoffNotice**(`doc`, `wallet`): `HTMLElement` \| `null`

Defined in: [app/walletHandoff.ts:143](https://github.com/asastats/frontend/blob/main/wallet/src/app/walletHandoff.ts#L143)

Explain the lost wallet step in the wallet's card, or at the top of the page.

## Parameters

### doc

`Document`

the page.

### wallet

[`HandoffWallet`](../interfaces/HandoffWallet.md)

the wallet that was open.

## Returns

`HTMLElement` \| `null`

the notice, or null when the page has nowhere to put it.
