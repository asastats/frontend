[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [main](../README.md) / App

# Class: App

Defined in: [main.ts:18](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L18)

Bootstraps the wallet-connect experience on the ASA Stats authorize page.

Initializes only when wallet card elements are present, fetches the list of
supported wallets from the backend, builds a mainnet `WalletManager`, binds a
`WalletComponent` per wallet, and resumes any prior sessions. There is no
network selector: ASA Stats authorizes on mainnet only.

## Constructors

### Constructor

> **new App**(): `App`

Defined in: [main.ts:27](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L27)

Registers initialization on `DOMContentLoaded`.

#### Returns

`App`

## Properties

### apiBase

> `private` **apiBase**: `string` = `DEFAULT_API_BASE`

Defined in: [main.ts:24](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L24)

Resolved walletauth API base path.

***

### walletComponents

> `private` **walletComponents**: [`WalletComponent`](../../walletComponent/classes/WalletComponent.md)[] = `[]`

Defined in: [main.ts:22](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L22)

Bound wallet components, retained for cleanup.

***

### walletManager

> **walletManager**: `WalletManager` \| `null` = `null`

Defined in: [main.ts:20](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L20)

The wallet manager, or null until [App.init](#init) runs.

## Methods

### init()

> **init**(): `Promise`\<`void`\>

Defined in: [main.ts:37](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L37)

Initializes wallets and binds components.

No-ops on pages without wallet cards. On failure it reveals the
`#app-error` element if present and logs the error.

#### Returns

`Promise`\<`void`\>
