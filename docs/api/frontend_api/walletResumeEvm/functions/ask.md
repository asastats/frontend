[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResumeEvm](../README.md) / ask

# Function: ask()

> **ask**(`container`, `text`, `yes`, `onYes`, `onNo`, `handsOff?`): `HTMLElement`

Defined in: [walletResumeEvm.ts:345](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L345)

Ask a question in the notice with a yes and a no button (V4).

## Parameters

### container

`HTMLElement`

`#evm-wallet-connect`.

### text

`string`

the question.

### yes

`string`

the yes button's label.

### onYes

() => `Promise`\<`void`\>

runs once on yes.

### onNo

() => `Promise`\<`void`\>

runs once on no.

### handsOff?

`boolean` = `false`

whether yes opens the wallet (app/walletHandoff.ts notes it).

## Returns

`HTMLElement`

the notice.
