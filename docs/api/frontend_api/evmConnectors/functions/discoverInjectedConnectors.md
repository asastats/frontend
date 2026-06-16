[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [evmConnectors](../README.md) / discoverInjectedConnectors

# Function: discoverInjectedConnectors()

> **discoverInjectedConnectors**(`timeoutMs?`): `Promise`\<[`EvmConnector`](../../evmWalletComponent/interfaces/EvmConnector.md)[]\>

Defined in: [evmConnectors.ts:29](https://github.com/asastats/frontend/blob/main/frontend/src/evmConnectors.ts#L29)

Discover injected EVM wallets via EIP-6963. Dispatches the request event and
collects announcements for a short window, returning one connector per wallet.

## Parameters

### timeoutMs?

`number` = `300`

Collection window for announcements.

## Returns

`Promise`\<[`EvmConnector`](../../evmWalletComponent/interfaces/EvmConnector.md)[]\>

Connectors for every announced injected wallet.
