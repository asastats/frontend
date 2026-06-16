[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [manageAdapters](../README.md) / ManageAdapterOptions

# Interface: ManageAdapterOptions

Defined in: [manageAdapters.ts:16](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L16)

Options for [defaultManageDeps](../functions/defaultManageDeps.md).

## Properties

### addPanel

> **addPanel**: `HTMLElement`

Defined in: [manageAdapters.ts:22](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L22)

Panel revealed to host the add-address connector buttons.

***

### algorandStepUpSign?

> `optional` **algorandStepUpSign?**: (`address`, `message`) => `Promise`\<`Record`\<`string`, `unknown`\>\>

Defined in: [manageAdapters.ts:29](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L29)

Step-up signing for an Algorand primary: build and sign the self-payment
challenge transaction (note = ``message``) and return the verify payload.
Wire this to the existing Algorand `WalletComponent`; without it, an
Algorand primary cannot complete step-up.

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

Defined in: [manageAdapters.ts:18](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L18)

walletauth API base (e.g. `/api/v2/wallet`).

***

### navigate?

> `optional` **navigate?**: (`url`) => `void`

Defined in: [manageAdapters.ts:34](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L34)

Navigation side effect (defaults to `window.location`).

#### Parameters

##### url

`string`

#### Returns

`void`

***

### wcProjectId

> **wcProjectId**: `string`

Defined in: [manageAdapters.ts:20](https://github.com/asastats/frontend/blob/main/frontend/src/manageAdapters.ts#L20)

WalletConnect project id; empty string means injected wallets only.
