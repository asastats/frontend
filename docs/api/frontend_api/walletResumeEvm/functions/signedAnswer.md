[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResumeEvm](../README.md) / signedAnswer

# Function: signedAnswer()

> **signedAnswer**(`provider`, `step`): \{ `record`: [`WcHistoryRecord`](../interfaces/WcHistoryRecord.md); `signature`: `string`; \} \| `null`

Defined in: [walletResumeEvm.ts:235](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L235)

The wallet's answer to our sign request, if the library has stored it (V2).

## Parameters

### provider

[`RestoredProvider`](../interfaces/RestoredProvider.md)

the restored provider.

### step

[`EvmSignStep`](../interfaces/EvmSignStep.md)

the sign step.

## Returns

\{ `record`: [`WcHistoryRecord`](../interfaces/WcHistoryRecord.md); `signature`: `string`; \} \| `null`

the signature and its record, or null.
