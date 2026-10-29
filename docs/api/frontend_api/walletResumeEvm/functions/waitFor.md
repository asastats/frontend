[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResumeEvm](../README.md) / waitFor

# Function: waitFor()

> **waitFor**\<`T`\>(`check`, `wait?`, `every?`): `Promise`\<`T` \| `null`\>

Defined in: [walletResumeEvm.ts:285](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L285)

Resolve with `check()`'s first truthy value, polling until `wait` ms pass.

## Type Parameters

### T

`T`

## Parameters

### check

() => `T` \| `null`

what to look for.

### wait?

`number` = `ANSWER_WAIT_MS`

how long, in ms.

### every?

`number` = `500`

poll interval, in ms.

## Returns

`Promise`\<`T` \| `null`\>

the value, or null.
