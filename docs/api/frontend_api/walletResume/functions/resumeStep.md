[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / resumeStep

# Function: resumeStep()

> **resumeStep**(`href`, `storage?`, `open?`, `now?`, `wait?`): `Promise`\<[`Resumed`](../type-aliases/Resumed.md)\>

Defined in: [walletResume.ts:507](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L507)

On page load, finish this page's pending step if the wallet answered.

## Parameters

### href

`string`

this page.

### storage?

`Storage` = `localStorage`

localStorage.

### open?

[`OpenSocket`](../type-aliases/OpenSocket.md) = `...`

opens the bridge socket.

### now?

`number` = `...`

the time, in ms.

### wait?

`number` = `ANSWER_WAIT_MS`

how long to wait for the answer, in ms.

## Returns

`Promise`\<[`Resumed`](../type-aliases/Resumed.md)\>

what happened.
