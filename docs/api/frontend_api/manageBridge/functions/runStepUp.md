[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [manageBridge](../README.md) / runStepUp

# Function: runStepUp()

> **runStepUp**(`req`, `deps`): `Promise`\<`void`\>

Defined in: [manageBridge.ts:42](https://github.com/asastats/frontend/blob/main/wallet/src/manageBridge.ts#L42)

Obtain a step-up challenge, sign the *operation-bound* message with the
current primary, then hand the proof to htmx to POST and swap in the refreshed
address list.

The signed message is `prefix + "{nonce}:{operation}:{targetId}"`, matching
what the server reconstructs and verifies, so a signature obtained for one
action cannot be redirected to another. Pure orchestration: every browser,
wallet and htmx concern is injected, so this is unit-tested.

## Parameters

### req

[`StepUpRequest`](../interfaces/StepUpRequest.md)

The requested operation and target.

### deps

[`RunStepUpDeps`](../interfaces/RunStepUpDeps.md)

Injected fetch / signer / ajax collaborators.

## Returns

`Promise`\<`void`\>
