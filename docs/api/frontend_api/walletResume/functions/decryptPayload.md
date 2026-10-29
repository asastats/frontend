[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / decryptPayload

# Function: decryptPayload()

> **decryptPayload**(`payload`, `keyHex`, `subtle?`): `Promise`\<`Record`\<`string`, `unknown`\> \| `null`\>

Defined in: [walletResume.ts:281](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L281)

Decrypt a WalletConnect v1 payload, checking its HMAC first (R1).

## Parameters

### payload

`string`

the bridge message's `payload`: JSON `{data, hmac, iv}` in hex.

### keyHex

`string`

the session key.

### subtle?

`SubtleCrypto` = `crypto.subtle`

WebCrypto.

## Returns

`Promise`\<`Record`\<`string`, `unknown`\> \| `null`\>

the JSON-RPC message, or null for anything that does not verify.
