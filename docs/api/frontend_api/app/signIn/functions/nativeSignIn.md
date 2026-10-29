[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/signIn](../README.md) / nativeSignIn

# Function: nativeSignIn()

> **nativeSignIn**(`provider`, `process`, `next`, `say`): `Promise`\<`"sent"` \| `"fallback"` \| `"stopped"`\>

Defined in: [app/signIn.ts:197](https://github.com/asastats/frontend/blob/main/wallet/src/app/signIn.ts#L197)

Sign in or connect with a native sheet.

## Parameters

### provider

`string`

`apple` or `google`.

### process

`"connect"` \| `"login"`

`login`, or `connect` on the Connections page.

### next

`string` \| `undefined`

where a login lands.

### say

(`message`) => `void`

shows a message to the reader.

## Returns

`Promise`\<`"sent"` \| `"fallback"` \| `"stopped"`\>

`sent` when the token form was posted, `fallback` when the phone has
  no account for the sheet, `stopped` otherwise.
