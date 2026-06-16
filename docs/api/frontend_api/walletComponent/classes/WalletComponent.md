[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletComponent](../README.md) / WalletComponent

# Class: WalletComponent

Defined in: [walletComponent.ts:53](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L53)

Manages a single Algorand wallet's connection and the address-authorization
flow for the ASA Stats authorize page.

Each supported wallet is rendered as its own card and driven by one
`WalletComponent`. The component reflects connection/active state into the
card's controls and, on authorize, proves control of the active account by
signing a 0-ALGO self-payment whose note carries a server nonce. The signed
transaction is posted to the backend for off-chain verification and is never
submitted to the network.

Authorize does not log the user in: the user is already authenticated, and a
successful verify authorizes the address onto their profile, then redirects
to the profile page.

## Example

```typescript
const component = new WalletComponent(wallet, manager);
component.bind(document.getElementById("wallet-pera")!);
```

## Constructors

### Constructor

> **new WalletComponent**(`wallet`, `manager`, `apiBase?`): `WalletComponent`

Defined in: [walletComponent.ts:72](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L72)

#### Parameters

##### wallet

`BaseWallet`

The wallet instance to manage.

##### manager

`WalletManager`

The wallet manager providing the algod client.

##### apiBase?

`string` = `DEFAULT_API_BASE`

Base path of the walletauth API (default
  `/api/v2/wallet`); pass a different value when the API is mounted
  elsewhere in a fork.

#### Returns

`WalletComponent`

## Properties

### apiBase

> `private` **apiBase**: `string`

Defined in: [walletComponent.ts:59](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L59)

Base path of the walletauth API endpoints.

***

### element

> `private` **element**: `HTMLElement` \| `null` = `null`

Defined in: [walletComponent.ts:63](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L63)

The bound DOM root of this wallet's card, or null before `bind`.

***

### manager

> **manager**: `WalletManager`

Defined in: [walletComponent.ts:57](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L57)

The wallet manager, used here for its configured algod client.

***

### unsubscribe?

> `private` `optional` **unsubscribe?**: () => `void`

Defined in: [walletComponent.ts:61](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L61)

Unsubscribe handle returned by `wallet.subscribe`.

#### Returns

`void`

***

### wallet

> **wallet**: `BaseWallet`

Defined in: [walletComponent.ts:55](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L55)

The wallet instance this component manages.

## Methods

### addEventListeners()

> **addEventListeners**(): `void`

Defined in: [walletComponent.ts:345](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L345)

Wires click and change delegation on the card root.

Clicks are routed by element id to connect/disconnect/set-active/authorize;
a change on the account `<select>` updates the active account.

#### Returns

`void`

***

### auth()

> **auth**(): `Promise`\<`void`\>

Defined in: [walletComponent.ts:255](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L255)

Authorizes the active account against the backend.

Flow: fetch a nonce for the active address, sign a 0-ALGO self-payment
whose note is `prefix + nonce`, post the signed transaction to
`<apiBase>/verify/` with `chain: "algorand"`, then redirect to the URL the
server returns (the profile page). The `chain` field lets the deferred EVM
branch slot in without a request reshape.

#### Returns

`Promise`\<`void`\>

***

### bind()

> **bind**(`element`): `void`

Defined in: [walletComponent.ts:90](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L90)

Binds the component to its card element and wires event listeners.

#### Parameters

##### element

`HTMLElement`

The wallet card root (`#wallet-<id>`).

#### Returns

`void`

***

### connect()

> **connect**(): `Promise`\<`void`\>

Defined in: [walletComponent.ts:184](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L184)

Connects the wallet.

#### Returns

`Promise`\<`void`\>

***

### destroy()

> **destroy**(): `void`

Defined in: [walletComponent.ts:376](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L376)

Tears down the wallet state subscription.

Should be called when the component is discarded to avoid leaks.

#### Returns

`void`

***

### disconnect()

> **disconnect**(): `Promise`\<`void`\>

Defined in: [walletComponent.ts:189](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L189)

Disconnects the wallet and clears its session.

#### Returns

`Promise`\<`void`\>

***

### getCsrfToken()

> `private` **getCsrfToken**(): `string`

Defined in: [walletComponent.ts:203](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L203)

Reads the CSRF token from the cookie, falling back to a hidden input.

#### Returns

`string`

The CSRF token, or an empty string when none is present.

***

### render()

> `private` **render**(`state`): `void`

Defined in: [walletComponent.ts:110](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L110)

Reflects the current wallet state into the card's controls.

Toggles button visibility, maintains the "Active" badge on the card
heading, and repopulates the account dropdown. All lookups are null-safe so
a card may omit controls it does not need (e.g. there is no test-transaction
button on the authorize page).

#### Parameters

##### state

Current wallet connection/active snapshot.

###### accounts

`any`[]

Connected accounts.

###### activeAccount

`any`

The currently active account, if any.

###### isActive

`boolean`

Whether this wallet is the active wallet.

###### isConnected

`boolean`

Whether the wallet is connected.

#### Returns

`void`

***

### setActive()

> **setActive**(): `Promise`\<`void`\>

Defined in: [walletComponent.ts:194](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L194)

Makes this wallet the active wallet for signing.

#### Returns

`Promise`\<`void`\>

***

### setActiveAccount()

> **setActiveAccount**(`event`): `Promise`\<`void`\>

Defined in: [walletComponent.ts:333](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L333)

Sets the active account from the dropdown selection.

#### Parameters

##### event

`Event`

The `change` event from the account `<select>`.

#### Returns

`Promise`\<`void`\>

***

### showError()

> `private` **showError**(`message`): `void`

Defined in: [walletComponent.ts:229](https://github.com/asastats/frontend/blob/main/frontend/src/walletComponent.ts#L229)

Surfaces an error to the user via a Materialize toast when available,
otherwise appends a transient message node to the card.

The message can contain wallet-derived text (e.g. an active account
address), so it is HTML-escaped before being handed to the toast, whose
`html` option is inserted as markup. The DOM fallback uses `textContent`
and is already safe.

#### Parameters

##### message

`string`

Human-readable error text (treated as untrusted).

#### Returns

`void`
