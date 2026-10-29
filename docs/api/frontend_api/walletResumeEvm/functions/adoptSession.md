[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResumeEvm](../README.md) / adoptSession

# Function: adoptSession()

> **adoptSession**(`provider`): [`WcSession`](../interfaces/WcSession.md) \| `undefined`

Defined in: [walletResumeEvm.ts:191](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L191)

The newest session the sign client holds, made the provider's own.

The provider takes the client's first session once, at init, so a connect the
wallet approves while the page restores, or after an older session, is not
its own yet (docs/logbook.md).

## Parameters

### provider

[`RestoredProvider`](../interfaces/RestoredProvider.md)

the restored provider.

## Returns

[`WcSession`](../interfaces/WcSession.md) \| `undefined`

the session, or undefined.
