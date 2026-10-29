[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResumeEvm](../README.md) / resumeEvm

# Function: resumeEvm()

> **resumeEvm**(`container`, `host`, `step`, `restore`, `wait?`): `Promise`\<[`EvmResumed`](../type-aliases/EvmResumed.md)\>

Defined in: [walletResumeEvm.ts:391](https://github.com/asastats/frontend/blob/main/wallet/src/walletResumeEvm.ts#L391)

After a restart, finish the EVM step the phone interrupted, asking first.

## Parameters

### container

`HTMLElement`

`#evm-wallet-connect`.

### host

[`EvmResumeHost`](../interfaces/EvmResumeHost.md)

the component on this page.

### step

[`EvmStep`](../type-aliases/EvmStep.md)

the step taken from storage.

### restore

() => `Promise`\<[`RestoredProvider`](../interfaces/RestoredProvider.md)\>

inits WalletConnect without its modal.

### wait?

`number` = `ANSWER_WAIT_MS`

how long to wait for the session or the answer, in ms.

## Returns

`Promise`\<[`EvmResumed`](../type-aliases/EvmResumed.md)\>

what was offered.
