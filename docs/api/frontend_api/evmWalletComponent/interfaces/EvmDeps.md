[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmWalletComponent](../README.md) / EvmDeps

# Interface: EvmDeps

Defined in: [evmWalletComponent.ts:57](https://github.com/asastats/frontend/blob/main/frontend/src/evmWalletComponent.ts#L57)

Injected collaborators; defaulted to viem/browser implementations in bootstrap.

## Properties

### fetchFn?

> `optional` **fetchFn?**: \{(`input`, `init?`): `Promise`\<`Response`\>; (`input`, `init?`): `Promise`\<`Response`\>; \}

Defined in: [evmWalletComponent.ts:63](https://github.com/asastats/frontend/blob/main/frontend/src/evmWalletComponent.ts#L63)

`fetch` implementation (defaults to the global).

#### Call Signature

> (`input`, `init?`): `Promise`\<`Response`\>

[MDN Reference](https://developer.mozilla.org/docs/Web/API/Window/fetch)

##### Parameters

###### input

`URL` \| `RequestInfo`

###### init?

`RequestInit`

##### Returns

`Promise`\<`Response`\>

#### Call Signature

> (`input`, `init?`): `Promise`\<`Response`\>

[MDN Reference](https://developer.mozilla.org/docs/Web/API/Window/fetch)

##### Parameters

###### input

`string` \| `URL` \| `Request`

###### init?

`RequestInit`

##### Returns

`Promise`\<`Response`\>

***

### listConnectors

> **listConnectors**: () => [`EvmConnector`](EvmConnector.md)[] \| `Promise`\<[`EvmConnector`](EvmConnector.md)[]\>

Defined in: [evmWalletComponent.ts:59](https://github.com/asastats/frontend/blob/main/frontend/src/evmWalletComponent.ts#L59)

Returns the connectors to offer (injected discovery + WalletConnect).

#### Returns

[`EvmConnector`](EvmConnector.md)[] \| `Promise`\<[`EvmConnector`](EvmConnector.md)[]\>

***

### navigate?

> `optional` **navigate?**: (`url`) => `void`

Defined in: [evmWalletComponent.ts:65](https://github.com/asastats/frontend/blob/main/frontend/src/evmWalletComponent.ts#L65)

Navigation side effect on success (defaults to `window.location`).

#### Parameters

##### url

`string`

#### Returns

`void`

***

### sign

> **sign**: [`EvmSigner`](../type-aliases/EvmSigner.md)

Defined in: [evmWalletComponent.ts:61](https://github.com/asastats/frontend/blob/main/frontend/src/evmWalletComponent.ts#L61)

Produces a signature for the challenge message.
