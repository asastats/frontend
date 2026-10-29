[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / acceptSignature

# Function: acceptSignature()

> **acceptSignature**(`step`): (`message`) => `string` \| `false` \| `null`

Defined in: [walletResume.ts:414](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L414)

Accept only a signature of this sign-in proof (R2): one signed 0-ALGO
self-payment from the step's address with exactly the step's note.

## Parameters

### step

[`SignStep`](../interfaces/SignStep.md)

the sign step.

## Returns

the signed transaction in base64, `false`, or null.

(`message`) => `string` \| `false` \| `null`
