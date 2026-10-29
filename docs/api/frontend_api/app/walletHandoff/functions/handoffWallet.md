[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/walletHandoff](../README.md) / handoffWallet

# Function: handoffWallet()

> **handoffWallet**(`target`): [`HandoffWallet`](../interfaces/HandoffWallet.md) \| `null`

Defined in: [app/walletHandoff.ts:48](https://github.com/asastats/frontend/blob/main/wallet/src/app/walletHandoff.ts#L48)

The wallet behind a tapped hand-off button, or null for any other click.

## Parameters

### target

`EventTarget` \| `null`

the clicked element.

## Returns

[`HandoffWallet`](../interfaces/HandoffWallet.md) \| `null`

the wallet's id and card title.
