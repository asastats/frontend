[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [main](../README.md) / App

# Class: App

Defined in: [main.ts:38](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L38)

Bootstraps the wallet-connect experience on the website authorize page.

Initializes only when wallet card elements are present, fetches the list of
supported wallets from the backend, builds a mainnet `WalletManager`, binds a
`WalletComponent` per wallet, and resumes any prior sessions. There is no
network selector: website authorizes on mainnet only.

## Constructors

### Constructor

> **new App**(): `App`

Defined in: [main.ts:47](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L47)

Installs the logout hook; `init` is started by the bootstrap below.

#### Returns

`App`

## Properties

### apiBase

> `private` **apiBase**: `string` = `DEFAULT_API_BASE`

Defined in: [main.ts:44](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L44)

Resolved walletauth API base path.

***

### walletComponents

> `private` **walletComponents**: [`WalletComponent`](../../walletComponent/classes/WalletComponent.md)[] = `[]`

Defined in: [main.ts:42](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L42)

Bound wallet components, retained for cleanup.

***

### walletManager

> **walletManager**: `WalletManager` \| `null` = `null`

Defined in: [main.ts:40](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L40)

The wallet manager, or null until [App.init](#init) runs.

## Methods

### explain()

> `private` **explain**(`resumed`): `void`

Defined in: [main.ts:137](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L137)

Tell the reader how the resumed step ended.

#### Parameters

##### resumed

[`Resumed`](../../walletResume/type-aliases/Resumed.md)

from [App.resume](#resume).

#### Returns

`void`

***

### init()

> **init**(): `Promise`\<`void`\>

Defined in: [main.ts:57](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L57)

Initializes wallets and binds components.

No-ops on pages without wallet cards. On failure it reveals the
`#app-error` element if present and logs the error.

#### Returns

`Promise`\<`void`\>

***

### resume()

> `private` **resume**(): `Promise`\<[`Resumed`](../../walletResume/type-aliases/Resumed.md)\>

Defined in: [main.ts:122](https://github.com/asastats/frontend/blob/main/wallet/src/main.ts#L122)

In the app, finish a step the phone interrupted (walletResume.ts).

#### Returns

`Promise`\<[`Resumed`](../../walletResume/type-aliases/Resumed.md)\>

what was found.
