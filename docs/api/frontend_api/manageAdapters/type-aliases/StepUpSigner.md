[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [manageAdapters](../README.md) / StepUpSigner

# Type Alias: StepUpSigner

> **StepUpSigner** = (`address`, `chain`, `message`) => `Promise`\<`Record`\<`string`, `unknown`\>\>

Defined in: [manageAdapters.ts:14](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L14)

Signs `message` with the wallet holding `address` on `chain`; resolves to the
proof fragment merged into the step-up POST (`{ signature }` for EVM,
`{ signedTransaction }` for Algorand). Rejects if the connected account is not
the primary, so step-up can only be met by the real primary key.

## Parameters

### address

`string`

### chain

`string`

### message

`string`

## Returns

`Promise`\<`Record`\<`string`, `unknown`\>\>
