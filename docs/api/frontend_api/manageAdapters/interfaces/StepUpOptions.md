[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [manageAdapters](../README.md) / StepUpOptions

# Interface: StepUpOptions

Defined in: [manageAdapters.ts:20](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L20)

Options for [buildStepUpSign](../functions/buildStepUpSign.md).

## Properties

### algorandStepUpSign?

> `optional` **algorandStepUpSign?**: (`address`, `message`) => `Promise`\<`Record`\<`string`, `unknown`\>\>

Defined in: [manageAdapters.ts:26](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L26)

Optional override for Algorand step-up signing (built-in is used otherwise).

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

Defined in: [manageAdapters.ts:22](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L22)

Walletauth API base, e.g. "/api/v2/wallet" (used for the wallets list).

***

### wcProjectId

> **wcProjectId**: `string`

Defined in: [manageAdapters.ts:24](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L24)

WalletConnect project id; empty string means injected wallets only.
