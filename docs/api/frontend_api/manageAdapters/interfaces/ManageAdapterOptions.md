[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [manageAdapters](../README.md) / ManageAdapterOptions

# Interface: ManageAdapterOptions

Defined in: [manageAdapters.ts:21](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L21)

Options for [defaultManageDeps](../functions/defaultManageDeps.md).

## Properties

### addUrl

> **addUrl**: `string`

Defined in: [manageAdapters.ts:27](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L27)

URL of the link page to add a new address (any chain).

***

### algorandStepUpSign?

> `optional` **algorandStepUpSign?**: (`address`, `message`) => `Promise`\<`Record`\<`string`, `unknown`\>\>

Defined in: [manageAdapters.ts:33](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L33)

Optional override for Algorand step-up signing. When omitted, the built-in
use-wallet signer is used (resumes the session of the wallet the user signed
in with and signs with it). Inject this only to customise the flow.

#### Parameters

##### address

`string`

##### message

`string`

#### Returns

`Promise`\<`Record`\<`string`, `unknown`\>\>

***

### apiBase

> **apiBase**: `string`

Defined in: [manageAdapters.ts:23](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L23)

Walletauth API base, e.g. "/api/v2/wallet" (used for the wallets list).

***

### navigate?

> `optional` **navigate?**: (`url`) => `void`

Defined in: [manageAdapters.ts:38](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L38)

Navigation side effect (defaults to `window.location`).

#### Parameters

##### url

`string`

#### Returns

`void`

***

### wcProjectId

> **wcProjectId**: `string`

Defined in: [manageAdapters.ts:25](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L25)

WalletConnect project id; empty string means injected wallets only.
