[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [manageAdapters](../README.md) / ManageAdapterOptions

# Interface: ManageAdapterOptions

Defined in: [manageAdapters.ts:16](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L16)

Options for [defaultManageDeps](../functions/defaultManageDeps.md).

## Properties

### addUrl

> **addUrl**: `string`

Defined in: [manageAdapters.ts:20](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L20)

URL of the link page to add a new address (any chain).

***

### algorandStepUpSign?

> `optional` **algorandStepUpSign?**: (`address`, `message`) => `Promise`\<`Record`\<`string`, `unknown`\>\>

Defined in: [manageAdapters.ts:27](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L27)

Step-up signing for an Algorand primary: build and sign the self-payment
challenge transaction (note = ``message``) and return the verify payload
(e.g. ``{ address, signedTransaction }``). Wire this to the Algorand
use-wallet stack; without it, an Algorand primary cannot complete step-up.

#### Parameters

##### address

`string`

##### message

`string`

#### Returns

`Promise`\<`Record`\<`string`, `unknown`\>\>

***

### navigate?

> `optional` **navigate?**: (`url`) => `void`

Defined in: [manageAdapters.ts:32](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L32)

Navigation side effect (defaults to `window.location`).

#### Parameters

##### url

`string`

#### Returns

`void`

***

### wcProjectId

> **wcProjectId**: `string`

Defined in: [manageAdapters.ts:18](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L18)

WalletConnect project id; empty string means injected wallets only.
