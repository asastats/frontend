[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletAdapters](../README.md) / uint8ArrayToBase64

# Function: uint8ArrayToBase64()

> **uint8ArrayToBase64**(`bytes`): `string`

Defined in: walletAdapters.ts:66

Safely converts a Uint8Array of arbitrary size to a Base64 string
without exceeding JavaScript engine call-stack argument limits.

## Parameters

### bytes

`Uint8Array`

The binary data to encode.

## Returns

`string`

Standard Base64 string.
