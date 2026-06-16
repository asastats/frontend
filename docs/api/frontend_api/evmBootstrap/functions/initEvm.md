[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [evmBootstrap](../README.md) / initEvm

# Function: initEvm()

> **initEvm**(`deps?`, `doc?`): `Promise`\<[`EvmWalletComponent`](../../EvmWalletComponent/classes/EvmWalletComponent.md) \| `null`\>

Defined in: [evmBootstrap.ts:31](https://github.com/asastats/frontend/blob/main/frontend/src/evmBootstrap.ts#L31)

Mount the EVM wallet UI when its container is present.

Reads `data-api-base` (login vs link mount point) and `data-wc-project-id`
(empty disables WalletConnect, leaving injected wallets only) from
`#evm-wallet-connect`, then renders and binds an [EvmWalletComponent](../../EvmWalletComponent/classes/EvmWalletComponent.md).
No-ops when the container is absent, so it is safe to call on every page.

The real browser/viem adapters are imported lazily and only when no deps are
injected, keeping those libraries out of the test path.

## Parameters

### deps?

`Partial`\<[`EvmBootstrapDeps`](../interfaces/EvmBootstrapDeps.md)\> = `{}`

Optional injected factories (used by tests).

### doc?

`Document` = `document`

Document to query (defaults to the global document).

## Returns

`Promise`\<[`EvmWalletComponent`](../../EvmWalletComponent/classes/EvmWalletComponent.md) \| `null`\>

The mounted component, or null when no container is present.
