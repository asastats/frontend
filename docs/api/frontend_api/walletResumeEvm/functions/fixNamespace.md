[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResumeEvm](../README.md) / fixNamespace

# Function: fixNamespace()

> **fixNamespace**(`provider`): `void`

Defined in: [walletResumeEvm.ts:209](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L209)

Give a restored provider its session's methods back.

Its rpc provider is rebuilt without them and then refuses `personal_sign`
(docs/logbook.md).

## Parameters

### provider

[`RestoredProvider`](../interfaces/RestoredProvider.md)

the restored provider.

## Returns

`void`
