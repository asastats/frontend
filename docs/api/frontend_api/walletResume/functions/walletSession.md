[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / walletSession

# Function: walletSession()

> **walletSession**(`wallet`): [`Session`](../interfaces/Session.md) \| `null`

Defined in: [walletResume.ts:100](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L100)

The WalletConnect session of a use-wallet Pera/Defly wallet, if it has one.

## Parameters

### wallet

`unknown`

a use-wallet wallet (its `client.connector.session`).

## Returns

[`Session`](../interfaces/Session.md) \| `null`

the session's fields, or null.
