[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResumeEvm](../README.md) / RestoredProvider

# Interface: RestoredProvider

Defined in: [walletResumeEvm.ts:61](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L61)

The `@walletconnect/ethereum-provider` surface the resume uses.

## Extends

- [`Eip1193Provider`](../../evmWalletComponent/interfaces/Eip1193Provider.md)

## Properties

### session?

> `optional` **session?**: [`WcSession`](WcSession.md)

Defined in: [walletResumeEvm.ts:62](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L62)

***

### signer

> **signer**: `object`

Defined in: [walletResumeEvm.ts:63](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L63)

#### client

> **client**: `object`

##### client.core

> **core**: `object`

##### client.core.history

> **history**: `object`

##### client.core.history.values

> **values**: [`WcHistoryRecord`](WcHistoryRecord.md)[]

##### client.core.history.delete()

> **delete**(`topic`, `id?`): `void`

###### Parameters

###### topic

`string`

###### id?

`number`

###### Returns

`void`

##### client.session?

> `optional` **session?**: `object`

##### client.session.getAll()

> **getAll**(): [`WcSession`](WcSession.md)[]

###### Returns

[`WcSession`](WcSession.md)[]

#### rpcProviders?

> `optional` **rpcProviders?**: `Record`\<`string`, \{ `namespace?`: \{ `methods?`: `unknown`; \}; `updateNamespace?`: `void`; \} \| `undefined`\>

#### session?

> `optional` **session?**: [`WcSession`](WcSession.md)

#### createProviders()?

> `optional` **createProviders**(): `void`

##### Returns

`void`

## Methods

### disconnect()

> **disconnect**(): `Promise`\<`void`\>

Defined in: [walletResumeEvm.ts:80](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L80)

#### Returns

`Promise`\<`void`\>

***

### request()

> **request**(`args`): `Promise`\<`unknown`\>

Defined in: [evmWalletComponent.ts:13](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L13)

#### Parameters

##### args

###### method

`string`

###### params?

`unknown`[]

#### Returns

`Promise`\<`unknown`\>

#### Inherited from

[`Eip1193Provider`](../../evmWalletComponent/interfaces/Eip1193Provider.md).[`request`](../../evmWalletComponent/interfaces/Eip1193Provider.md#request)
