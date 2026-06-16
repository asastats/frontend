[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [manageBootstrap](../README.md) / initManageAddresses

# Function: initManageAddresses()

> **initManageAddresses**(`deps?`, `doc?`): `Promise`\<[`ManageAddressesComponent`](../../ManageAddressesComponent/classes/ManageAddressesComponent.md) \| `null`\>

Defined in: [manageBootstrap.ts:20](https://github.com/asastats/frontend/blob/main/frontend/src/manageBootstrap.ts#L20)

Mount the connected-addresses manager when its container is present.

Reads `data-api-base` and `data-wc-project-id` from `#connected-addresses`,
then renders and binds a [ManageAddressesComponent](../../ManageAddressesComponent/classes/ManageAddressesComponent.md). No-ops when the
container is absent, so it is safe to call on every page. The browser/wallet
adapters are imported lazily and only when no deps are injected, keeping
viem/WalletConnect out of the test path.

## Parameters

### deps?

`Partial`\<[`ManageDeps`](../../ManageAddressesComponent/interfaces/ManageDeps.md)\> = `{}`

Optional injected dependencies (used by tests).

### doc?

`Document` = `document`

Document to query (defaults to the global document).

## Returns

`Promise`\<[`ManageAddressesComponent`](../../ManageAddressesComponent/classes/ManageAddressesComponent.md) \| `null`\>

The mounted component, or null when no container is present.
