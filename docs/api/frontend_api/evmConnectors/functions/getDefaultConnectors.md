[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [evmConnectors](../README.md) / getDefaultConnectors

# Function: getDefaultConnectors()

> **getDefaultConnectors**(`projectId`): `Promise`\<[`EvmConnector`](../../EvmWalletComponent/interfaces/EvmConnector.md)[]\>

Defined in: [evmConnectors.ts:104](https://github.com/asastats/frontend/blob/main/frontend/src/evmConnectors.ts#L104)

Default connector set: injected wallets discovered via EIP-6963, plus a
WalletConnect option when a project id is configured.

## Parameters

### projectId

`string`

WalletConnect project id (empty disables WalletConnect).

## Returns

`Promise`\<[`EvmConnector`](../../EvmWalletComponent/interfaces/EvmConnector.md)[]\>

The connectors to offer the user.
