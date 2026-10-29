[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmWalletComponent](../README.md) / EvmWalletComponent

# Class: EvmWalletComponent

Defined in: [evmWalletComponent.ts:69](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L69)

Drives the EVM / xChain wallet flow for both authentication (login) and
authorization (linking). The two modes differ only by `apiBase`
(`/api/v2/wallet/login` vs `/api/v2/wallet/link`); the request shape is
identical, mirroring the Algorand component.

Flow on selecting a connector: open the wallet, fetch a nonce for the
address, sign `prefix + nonce` (EIP-191 `personal_sign`), post
`{ nonce, chain: "evm", signature }` to `<apiBase>/verify/`, then navigate to
the URL the server returns. The wallet libraries are injected, so the
orchestration is exercised without a browser or a real wallet.

## Example

```typescript
const c = new EvmWalletComponent(el, "/api/v2/wallet/link", deps);
await c.bind();
```

## Constructors

### Constructor

> **new EvmWalletComponent**(`element`, `apiBase?`, `deps`): `EvmWalletComponent`

Defined in: [evmWalletComponent.ts:84](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L84)

#### Parameters

##### element

`HTMLElement`

Container element (`#evm-wallet-connect`).

##### apiBase?

`string` = `DEFAULT_EVM_API_BASE`

EVM API base; `/api/v2/wallet/login` or `.../link`.

##### deps

[`EvmDeps`](../interfaces/EvmDeps.md)

Injected wallet/network collaborators.

#### Returns

`EvmWalletComponent`

## Properties

### apiBase

> `private` **apiBase**: `string`

Defined in: [evmWalletComponent.ts:73](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L73)

Base path of the EVM walletauth endpoints.

***

### connectors

> `private` **connectors**: [`EvmConnector`](../interfaces/EvmConnector.md)[] = `[]`

Defined in: [evmWalletComponent.ts:77](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L77)

Connectors rendered on the last `render`, for click lookup.

***

### deps

> `private` **deps**: [`EvmDeps`](../interfaces/EvmDeps.md)

Defined in: [evmWalletComponent.ts:75](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L75)

Injected collaborators.

***

### element

> `private` **element**: `HTMLElement`

Defined in: [evmWalletComponent.ts:71](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L71)

The bound container (carries `#evm-wallet-list` and error slot).

## Methods

### addEventListeners()

> `private` **addEventListeners**(): `void`

Defined in: [evmWalletComponent.ts:184](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L184)

Wires click delegation; routes connector-button clicks to the flow.

#### Returns

`void`

***

### authorizeWith()

> **authorizeWith**(`connector`): `Promise`\<`boolean`\>

Defined in: [evmWalletComponent.ts:207](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L207)

Connects the chosen wallet and runs the nonce → sign → verify exchange.

#### Parameters

##### connector

[`EvmConnector`](../interfaces/EvmConnector.md)

The wallet the user selected.

#### Returns

`Promise`\<`boolean`\>

Whether the reader was signed in.

***

### bind()

> **bind**(): `Promise`\<`void`\>

Defined in: [evmWalletComponent.ts:95](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L95)

Discovers connectors, renders buttons, and wires click delegation.

#### Returns

`Promise`\<`void`\>

***

### connect()

> `private` **connect**(`connector`): `Promise`\<\{ `address`: `string`; `provider`: [`Eip1193Provider`](../interfaces/Eip1193Provider.md); \}\>

Defined in: [evmWalletComponent.ts:271](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L271)

Opens the wallet; WalletConnect's picker cannot show above the open login
dialog (top layer), so the dialog closes until the connect ends.

#### Parameters

##### connector

[`EvmConnector`](../interfaces/EvmConnector.md)

The wallet the user selected.

#### Returns

`Promise`\<\{ `address`: `string`; `provider`: [`Eip1193Provider`](../interfaces/Eip1193Provider.md); \}\>

The provider and address.

***

### getCsrfToken()

> `private` **getCsrfToken**(): `string`

Defined in: [evmWalletComponent.ts:156](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L156)

Reads the CSRF token from the cookie, falling back to a hidden input.

#### Returns

`string`

The CSRF token, or an empty string when none is present.

***

### headers()

> `private` **headers**(): `object`

Defined in: [evmWalletComponent.ts:337](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L337)

Shared headers, including CSRF for the session-authenticated link API.

#### Returns

`object`

##### Content-Type

> **Content-Type**: `string` = `"application/json"`

##### X-CSRFToken

> **X-CSRFToken**: `string`

***

### render()

> `private` **render**(): `Promise`\<`void`\>

Defined in: [evmWalletComponent.ts:105](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L105)

Renders one button per discovered connector into `#evm-wallet-list`
(falling back to the container itself). With no connectors, reveals the
`#evm-app-error` slot instead.

#### Returns

`Promise`\<`void`\>

***

### showError()

> `private` **showError**(`message`): `void`

Defined in: [evmWalletComponent.ts:179](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L179)

Surfaces an error through the host, falling back to a transient notice.

The message may carry wallet-derived text; every path renders it as
textContent, so it is never parsed as markup.

#### Parameters

##### message

`string`

Human-readable error text (treated as untrusted).

#### Returns

`void`

***

### showNoWallets()

> `private` **showNoWallets**(): `void`

Defined in: [evmWalletComponent.ts:142](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L142)

Reveals the no-wallet error banner when present.

#### Returns

`void`

***

### signInWith()

> **signInWith**(`provider`, `address`, `name`): `Promise`\<`boolean`\>

Defined in: [evmWalletComponent.ts:290](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L290)

Runs the sign-in with a provider that is already connected (a resumed session).

#### Parameters

##### provider

[`Eip1193Provider`](../interfaces/Eip1193Provider.md)

The connected provider.

##### address

`string`

Its address.

##### name

`string`

The wallet's name.

#### Returns

`Promise`\<`boolean`\>

Whether the reader was signed in.

***

### verify()

> **verify**(`apiBase`, `nonce`, `signature`, `binding`): `Promise`\<`boolean`\>

Defined in: [evmWalletComponent.ts:307](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L307)

Posts a signature to `<apiBase>/verify/` and follows the redirect.

#### Parameters

##### apiBase

`string`

The login or link API base.

##### nonce

`string`

The nonce that was signed.

##### signature

`string`

The EIP-191 signature.

##### binding

`string`

The page's login binding secret.

#### Returns

`Promise`\<`boolean`\>

Whether the reader was signed in.
