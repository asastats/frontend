[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [evmWalletComponent](../README.md) / EvmWalletComponent

# Class: EvmWalletComponent

Defined in: evmWalletComponent.ts:86

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

Defined in: evmWalletComponent.ts:101

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

Defined in: evmWalletComponent.ts:90

Base path of the EVM walletauth endpoints.

***

### connectors

> `private` **connectors**: [`EvmConnector`](../interfaces/EvmConnector.md)[] = `[]`

Defined in: evmWalletComponent.ts:94

Connectors rendered on the last `render`, for click lookup.

***

### deps

> `private` **deps**: [`EvmDeps`](../interfaces/EvmDeps.md)

Defined in: evmWalletComponent.ts:92

Injected collaborators.

***

### element

> `private` **element**: `HTMLElement`

Defined in: evmWalletComponent.ts:88

The bound container (carries `#evm-wallet-list` and error slot).

## Methods

### addEventListeners()

> `private` **addEventListeners**(): `void`

Defined in: evmWalletComponent.ts:209

Wires click delegation; routes connector-button clicks to the flow.

#### Returns

`void`

***

### authorizeWith()

> **authorizeWith**(`connector`): `Promise`\<`void`\>

Defined in: evmWalletComponent.ts:231

Connects the chosen wallet and runs the nonce → sign → verify exchange.

#### Parameters

##### connector

[`EvmConnector`](../interfaces/EvmConnector.md)

The wallet the user selected.

#### Returns

`Promise`\<`void`\>

***

### bind()

> **bind**(): `Promise`\<`void`\>

Defined in: evmWalletComponent.ts:112

Discovers connectors, renders buttons, and wires click delegation.

#### Returns

`Promise`\<`void`\>

***

### getCsrfToken()

> `private` **getCsrfToken**(): `string`

Defined in: evmWalletComponent.ts:172

Reads the CSRF token from the cookie, falling back to a hidden input.

#### Returns

`string`

The CSRF token, or an empty string when none is present.

***

### render()

> `private` **render**(): `Promise`\<`void`\>

Defined in: evmWalletComponent.ts:122

Renders one button per discovered connector into `#evm-wallet-list`
(falling back to the container itself). With no connectors, reveals the
`#evm-app-error` slot instead.

#### Returns

`Promise`\<`void`\>

***

### showError()

> `private` **showError**(`message`): `void`

Defined in: evmWalletComponent.ts:194

Surfaces an error via a Materialize toast when available, otherwise a
transient card panel. The message may carry wallet-derived text, so it is
HTML-escaped before being handed to the toast `html` sink.

#### Parameters

##### message

`string`

Human-readable error text (treated as untrusted).

#### Returns

`void`

***

### showNoWallets()

> `private` **showNoWallets**(): `void`

Defined in: evmWalletComponent.ts:158

Reveals the no-wallet error banner when present.

#### Returns

`void`
