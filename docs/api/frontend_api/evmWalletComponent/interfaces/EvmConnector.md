[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmWalletComponent](../README.md) / EvmConnector

# Interface: EvmConnector

Defined in: [evmWalletComponent.ts:17](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L17)

A selectable EVM wallet. Concrete connectors are produced by the browser-only
adapters in `evmConnectors.ts` (EIP-6963 injected wallets and WalletConnect),
but the component depends only on this shape so it stays testable.

## Properties

### icon?

> `optional` **icon?**: `string`

Defined in: [evmWalletComponent.ts:23](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L23)

Optional data-URI icon (EIP-6963 announces one).

***

### id

> **id**: `string`

Defined in: [evmWalletComponent.ts:19](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L19)

Stable identifier (EIP-6963 rdns, or `"walletconnect"`).

***

### name

> **name**: `string`

Defined in: [evmWalletComponent.ts:21](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L21)

Human-readable wallet name shown on the button.

## Methods

### connect()

> **connect**(): `Promise`\<\{ `address`: `string`; `provider`: [`Eip1193Provider`](Eip1193Provider.md); \}\>

Defined in: [evmWalletComponent.ts:25](https://github.com/asastats/frontend/blob/main/wallet/src/evmWalletComponent.ts#L25)

Opens the wallet and returns its provider and selected address.

#### Returns

`Promise`\<\{ `address`: `string`; `provider`: [`Eip1193Provider`](Eip1193Provider.md); \}\>
