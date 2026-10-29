[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmConnectors](../README.md) / restoreWalletConnect

# Function: restoreWalletConnect()

> **restoreWalletConnect**(`projectId`): `Promise`\<[`RestoredProvider`](../../walletResumeEvm/interfaces/RestoredProvider.md)\>

Defined in: [evmConnectors.ts:111](https://github.com/asastats/frontend/blob/main/wallet/src/evmConnectors.ts#L111)

Init WalletConnect without its modal, so it restores the session and answers
it stored before the phone closed the app (walletResumeEvm.ts).

## Parameters

### projectId

`string`

Reown/WalletConnect Cloud project id.

## Returns

`Promise`\<[`RestoredProvider`](../../walletResumeEvm/interfaces/RestoredProvider.md)\>

The provider, as the resume reads it.
