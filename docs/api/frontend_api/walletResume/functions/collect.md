[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / collect

# Function: collect()

> **collect**\<`T`\>(`step`, `accept`, `open`, `wait?`): `Promise`\<`T` \| `null`\>

Defined in: [walletResume.ts:316](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L316)

Wait on the bridge for the first message `accept` takes (R8: once, then close).

## Type Parameters

### T

`T`

## Parameters

### step

[`Step`](../type-aliases/Step.md)

the pending step.

### accept

(`message`) => `false` \| `T` \| `null`

returns a value for the wanted message, `false` for a
  refusal (stop), or null to keep waiting.

### open

[`OpenSocket`](../type-aliases/OpenSocket.md)

opens the socket.

### wait?

`number` = `ANSWER_WAIT_MS`

how long, in ms.

## Returns

`Promise`\<`T` \| `null`\>

the accepted value, or null.
