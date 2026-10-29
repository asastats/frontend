[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmBootstrap](../README.md) / EvmBootstrapDeps

# Interface: EvmBootstrapDeps

Defined in: [evmBootstrap.ts:11](https://github.com/asastats/frontend/blob/main/wallet/src/evmBootstrap.ts#L11)

Injectable factories so the bootstrap can be tested without viem/WalletConnect.

## Properties

### connectorFactory

> **connectorFactory**: (`projectId`) => [`EvmConnector`](../../evmWalletComponent/interfaces/EvmConnector.md)[] \| `Promise`\<[`EvmConnector`](../../evmWalletComponent/interfaces/EvmConnector.md)[]\>

Defined in: [evmBootstrap.ts:13](https://github.com/asastats/frontend/blob/main/wallet/src/evmBootstrap.ts#L13)

Builds the connector list for a given WalletConnect project id.

#### Parameters

##### projectId

`string`

#### Returns

[`EvmConnector`](../../evmWalletComponent/interfaces/EvmConnector.md)[] \| `Promise`\<[`EvmConnector`](../../evmWalletComponent/interfaces/EvmConnector.md)[]\>

***

### restore

> **restore**: (`projectId`) => `Promise`\<[`RestoredProvider`](../../walletResumeEvm/interfaces/RestoredProvider.md)\>

Defined in: [evmBootstrap.ts:17](https://github.com/asastats/frontend/blob/main/wallet/src/evmBootstrap.ts#L17)

Inits WalletConnect without its modal after a restart.

#### Parameters

##### projectId

`string`

#### Returns

`Promise`\<[`RestoredProvider`](../../walletResumeEvm/interfaces/RestoredProvider.md)\>

***

### signer

> **signer**: [`EvmSigner`](../../evmWalletComponent/type-aliases/EvmSigner.md)

Defined in: [evmBootstrap.ts:15](https://github.com/asastats/frontend/blob/main/wallet/src/evmBootstrap.ts#L15)

Signs the challenge message.
