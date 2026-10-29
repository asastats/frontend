[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/signIn](../README.md) / connect

# Function: connect()

> **connect**(`provider`, `say?`): `Promise`\<`boolean`\>

Defined in: [app/signIn.ts:267](https://github.com/asastats/frontend/blob/main/wallet/src/app/signIn.ts#L267)

Connect `provider` to the signed-in account with its native sheet.

## Parameters

### provider

`string`

`apple` or `google`.

### say?

(`message`) => `void`

shows a message to the reader.

## Returns

`Promise`\<`boolean`\>

whether the token form was sent.
