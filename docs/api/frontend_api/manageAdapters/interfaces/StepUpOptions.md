[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [manageAdapters](../README.md) / StepUpOptions

# Interface: StepUpOptions

Defined in: [manageAdapters.ts:21](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L21)

Options for [buildStepUpSign](../functions/buildStepUpSign.md).

## Properties

### algorandStepUpSign?

> `optional` **algorandStepUpSign?**: (`address`, `message`) => `Promise`\<`Record`\<`string`, `unknown`\>\>

Defined in: [manageAdapters.ts:27](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L27)

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

Defined in: [manageAdapters.ts:23](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L23)

Walletauth API base, e.g. "/api/v2/wallet" (used for the wallets list).

***

### wcProjectId

> **wcProjectId**: `string`

Defined in: [manageAdapters.ts:25](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L25)

WalletConnect project id; empty string means injected wallets only.
