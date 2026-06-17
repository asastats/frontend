[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmWalletComponent](../README.md) / EvmDeps

# Interface: EvmDeps

Defined in: [evmWalletComponent.ts:36](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L36)

Injected collaborators; defaulted to viem/browser implementations in bootstrap.

## Properties

### fetchFn?

> `optional` **fetchFn?**: \{(`input`, `init?`): `Promise`\<`Response`\>; (`input`, `init?`): `Promise`\<`Response`\>; \}

Defined in: [evmWalletComponent.ts:42](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L42)

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

Defined in: [evmWalletComponent.ts:38](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L38)

Returns the connectors to offer (injected discovery + WalletConnect).

#### Returns

[`EvmConnector`](EvmConnector.md)[] \| `Promise`\<[`EvmConnector`](EvmConnector.md)[]\>

***

### navigate?

> `optional` **navigate?**: (`url`) => `void`

Defined in: [evmWalletComponent.ts:44](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L44)

Navigation side effect on success (defaults to `window.location`).

#### Parameters

##### url

`string`

#### Returns

`void`

***

### sign

> **sign**: [`EvmSigner`](../type-aliases/EvmSigner.md)

Defined in: [evmWalletComponent.ts:40](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L40)

Produces a signature for the challenge message.
