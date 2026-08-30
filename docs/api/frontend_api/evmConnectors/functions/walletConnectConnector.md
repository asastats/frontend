[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmConnectors](../README.md) / walletConnectConnector

# Function: walletConnectConnector()

> **walletConnectConnector**(`projectId`): [`EvmConnector`](../../evmWalletComponent/interfaces/EvmConnector.md)

Defined in: [evmConnectors.ts:77](https://github.com/asastats/frontend/blob/main/wallet/src/evmConnectors.ts#L77)

Build a WalletConnect connector. The provider library is imported lazily so
the dependency only loads when a project id is configured and the user picks
WalletConnect.

## Parameters

### projectId

`string`

Reown/WalletConnect Cloud project id.

## Returns

[`EvmConnector`](../../evmWalletComponent/interfaces/EvmConnector.md)

A connector that opens the WalletConnect modal.
