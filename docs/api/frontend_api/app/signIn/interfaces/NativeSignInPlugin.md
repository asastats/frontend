[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/signIn](../README.md) / NativeSignInPlugin

# Interface: NativeSignInPlugin

Defined in: [app/signIn.ts:31](https://github.com/asastats/frontend/blob/main/wallet/src/app/signIn.ts#L31)

The local plugin in mobile/ (O3); app versions without it reject every call.

## Methods

### isAvailable()

> **isAvailable**(`options`): `Promise`\<\{ `available`: `boolean`; \}\>

Defined in: [app/signIn.ts:32](https://github.com/asastats/frontend/blob/main/wallet/src/app/signIn.ts#L32)

#### Parameters

##### options

###### provider

`string`

#### Returns

`Promise`\<\{ `available`: `boolean`; \}\>

***

### signIn()

> **signIn**(`options`): `Promise`\<[`NativeSignInResult`](NativeSignInResult.md)\>

Defined in: [app/signIn.ts:33](https://github.com/asastats/frontend/blob/main/wallet/src/app/signIn.ts#L33)

#### Parameters

##### options

###### nonce

`string`

###### provider

`string`

###### serverClientId?

`string`

#### Returns

`Promise`\<[`NativeSignInResult`](NativeSignInResult.md)\>
