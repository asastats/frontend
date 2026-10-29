[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/signIn](../README.md) / postForm

# Function: postForm()

> **postForm**(`action`, `fields`, `doc?`): `void`

Defined in: [app/signIn.ts:130](https://github.com/asastats/frontend/blob/main/wallet/src/app/signIn.ts#L130)

POST `fields` and the CSRF token as a hidden form, so nothing lands in
history and the server's answer (a redirect, a signup form) is the next page.

## Parameters

### action

`string`

same-site path.

### fields

`Record`\<`string`, `string`\>

the values to send.

### doc?

`Document` = `document`

the document to submit from.

## Returns

`void`
