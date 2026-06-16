[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [evmBootstrap](../README.md) / EvmBootstrapDeps

# Interface: EvmBootstrapDeps

Defined in: [evmBootstrap.ts:9](https://github.com/asastats/frontend/blob/main/frontend/src/evmBootstrap.ts#L9)

Injectable factories so the bootstrap can be tested without viem/WalletConnect.

## Properties

### connectorFactory

> **connectorFactory**: (`projectId`) => [`EvmConnector`](../../EvmWalletComponent/interfaces/EvmConnector.md)[] \| `Promise`\<[`EvmConnector`](../../EvmWalletComponent/interfaces/EvmConnector.md)[]\>

Defined in: [evmBootstrap.ts:11](https://github.com/asastats/frontend/blob/main/frontend/src/evmBootstrap.ts#L11)

Builds the connector list for a given WalletConnect project id.

#### Parameters

##### projectId

`string`

#### Returns

[`EvmConnector`](../../EvmWalletComponent/interfaces/EvmConnector.md)[] \| `Promise`\<[`EvmConnector`](../../EvmWalletComponent/interfaces/EvmConnector.md)[]\>

***

### signer

> **signer**: [`EvmSigner`](../../EvmWalletComponent/type-aliases/EvmSigner.md)

Defined in: [evmBootstrap.ts:13](https://github.com/asastats/frontend/blob/main/frontend/src/evmBootstrap.ts#L13)

Signs the challenge message.
