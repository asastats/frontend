[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [manageAdapters](../README.md) / buildStepUpSign

# Function: buildStepUpSign()

> **buildStepUpSign**(`options`): [`StepUpSigner`](../type-aliases/StepUpSigner.md)

Defined in: [manageAdapters.ts:113](https://github.com/asastats/frontend/blob/main/wallet/src/manageAdapters.ts#L113)

Build the [StepUpSigner](../type-aliases/StepUpSigner.md) for the manage page (EVM + Algorand).

## Parameters

### options

[`StepUpOptions`](../interfaces/StepUpOptions.md)

API base, WalletConnect id, optional Algorand override.

## Returns

[`StepUpSigner`](../type-aliases/StepUpSigner.md)

A signer the htmx bridge calls to obtain step-up proof.
