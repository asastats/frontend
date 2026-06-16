[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [EvmWalletComponent](../README.md) / EvmConnector

# Interface: EvmConnector

Defined in: [EvmWalletComponent.ts:38](https://github.com/asastats/frontend/blob/main/frontend/src/EvmWalletComponent.ts#L38)

A selectable EVM wallet. Concrete connectors are produced by the browser-only
adapters in `evmConnectors.ts` (EIP-6963 injected wallets and WalletConnect),
but the component depends only on this shape so it stays testable.

## Properties

### icon?

> `optional` **icon?**: `string`

Defined in: [EvmWalletComponent.ts:44](https://github.com/asastats/frontend/blob/main/frontend/src/EvmWalletComponent.ts#L44)

Optional data-URI icon (EIP-6963 announces one).

***

### id

> **id**: `string`

Defined in: [EvmWalletComponent.ts:40](https://github.com/asastats/frontend/blob/main/frontend/src/EvmWalletComponent.ts#L40)

Stable identifier (EIP-6963 rdns, or `"walletconnect"`).

***

### name

> **name**: `string`

Defined in: [EvmWalletComponent.ts:42](https://github.com/asastats/frontend/blob/main/frontend/src/EvmWalletComponent.ts#L42)

Human-readable wallet name shown on the button.

## Methods

### connect()

> **connect**(): `Promise`\<\{ `address`: `string`; `provider`: [`Eip1193Provider`](Eip1193Provider.md); \}\>

Defined in: [EvmWalletComponent.ts:46](https://github.com/asastats/frontend/blob/main/frontend/src/EvmWalletComponent.ts#L46)

Opens the wallet and returns its provider and selected address.

#### Returns

`Promise`\<\{ `address`: `string`; `provider`: [`Eip1193Provider`](Eip1193Provider.md); \}\>
