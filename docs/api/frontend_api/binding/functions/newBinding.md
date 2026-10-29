[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [binding](../README.md) / newBinding

# Function: newBinding()

> **newBinding**(): `string`

Defined in: [binding.ts:11](https://github.com/asastats/frontend/blob/main/wallet/src/binding.ts#L11)

A fresh secret for one sign-in attempt: sent with the nonce request and
again with the verify, which refuses the proof without it.

## Returns

`string`

32 random bytes as 64 lower-case hex characters (the server's `BINDING_RE`).
