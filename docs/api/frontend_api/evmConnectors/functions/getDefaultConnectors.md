[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmConnectors](../README.md) / getDefaultConnectors

# Function: getDefaultConnectors()

> **getDefaultConnectors**(`projectId`): `Promise`\<[`EvmConnector`](../../evmWalletComponent/interfaces/EvmConnector.md)[]\>

Defined in: [evmConnectors.ts:105](https://github.com/asastats/frontend/blob/main/wallet/src/evmConnectors.ts#L105)

Default connector set: injected wallets discovered via EIP-6963, plus a
WalletConnect option when a project id is configured.

## Parameters

### projectId

`string`

WalletConnect project id (empty disables WalletConnect).

## Returns

`Promise`\<[`EvmConnector`](../../evmWalletComponent/interfaces/EvmConnector.md)[]\>

The connectors to offer the user.
