[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmWalletComponent](../README.md) / EvmWalletComponent

# Class: EvmWalletComponent

Defined in: [evmWalletComponent.ts:67](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L67)

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

Defined in: [evmWalletComponent.ts:82](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L82)

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

Defined in: [evmWalletComponent.ts:71](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L71)

Base path of the EVM walletauth endpoints.

***

### connectors

> `private` **connectors**: [`EvmConnector`](../interfaces/EvmConnector.md)[] = `[]`

Defined in: [evmWalletComponent.ts:75](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L75)

Connectors rendered on the last `render`, for click lookup.

***

### deps

> `private` **deps**: [`EvmDeps`](../interfaces/EvmDeps.md)

Defined in: [evmWalletComponent.ts:73](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L73)

Injected collaborators.

***

### element

> `private` **element**: `HTMLElement`

Defined in: [evmWalletComponent.ts:69](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L69)

The bound container (carries `#evm-wallet-list` and error slot).

## Methods

### addEventListeners()

> `private` **addEventListeners**(): `void`

Defined in: [evmWalletComponent.ts:182](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L182)

Wires click delegation; routes connector-button clicks to the flow.

#### Returns

`void`

***

### authorizeWith()

> **authorizeWith**(`connector`): `Promise`\<`void`\>

Defined in: [evmWalletComponent.ts:204](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L204)

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

Defined in: [evmWalletComponent.ts:93](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L93)

Discovers connectors, renders buttons, and wires click delegation.

#### Returns

`Promise`\<`void`\>

***

### getCsrfToken()

> `private` **getCsrfToken**(): `string`

Defined in: [evmWalletComponent.ts:154](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L154)

Reads the CSRF token from the cookie, falling back to a hidden input.

#### Returns

`string`

The CSRF token, or an empty string when none is present.

***

### render()

> `private` **render**(): `Promise`\<`void`\>

Defined in: [evmWalletComponent.ts:103](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L103)

Renders one button per discovered connector into `#evm-wallet-list`
(falling back to the container itself). With no connectors, reveals the
`#evm-app-error` slot instead.

#### Returns

`Promise`\<`void`\>

***

### showError()

> `private` **showError**(`message`): `void`

Defined in: [evmWalletComponent.ts:177](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L177)

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

Defined in: [evmWalletComponent.ts:140](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L140)

Reveals the no-wallet error banner when present.

#### Returns

`void`
