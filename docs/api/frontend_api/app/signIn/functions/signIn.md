[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/signIn](../README.md) / signIn

# Function: signIn()

> **signIn**(`provider`, `next?`, `say?`): `Promise`\<`boolean`\>

Defined in: [app/signIn.ts:231](https://github.com/asastats/frontend/blob/main/wallet/src/app/signIn.ts#L231)

Sign in with `provider`: its native sheet where the phone has one, else the
system browser.

## Parameters

### provider

`string`

an allauth provider id, as `data-app-signin` names it.

### next?

`string` \| `undefined`

where to land; see `nextFor`.

### say?

(`message`) => `void`

shows a message to the reader.

## Returns

`Promise`\<`boolean`\>

whether the redeem form was sent.
