[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResumeEvm](../README.md) / EvmResumeHost

# Interface: EvmResumeHost

Defined in: [walletResumeEvm.ts:84](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L84)

What the restored page can do with the component that drew the buttons.

## Methods

### signInWith()

> **signInWith**(`provider`, `address`, `name`): `Promise`\<`boolean`\>

Defined in: [walletResumeEvm.ts:86](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L86)

Runs nonce, sign and verify with `provider`; resolves true once signed in.

#### Parameters

##### provider

[`Eip1193Provider`](../../evmWalletComponent/interfaces/Eip1193Provider.md)

##### address

`string`

##### name

`string`

#### Returns

`Promise`\<`boolean`\>

***

### verify()

> **verify**(`apiBase`, `nonce`, `signature`, `binding`): `Promise`\<`boolean`\>

Defined in: [walletResumeEvm.ts:88](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L88)

Posts a collected signature to verify and follows the redirect; true on success.

#### Parameters

##### apiBase

`string`

##### nonce

`string`

##### signature

`string`

##### binding

`string`

#### Returns

`Promise`\<`boolean`\>
