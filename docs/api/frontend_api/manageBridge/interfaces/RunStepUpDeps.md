[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [manageBridge](../README.md) / RunStepUpDeps

# Interface: RunStepUpDeps

Defined in: manageBridge.ts:14

Injected collaborators for [runStepUp](../functions/runStepUp.md) (all browser concerns isolated).

## Properties

### ajax

> **ajax**: (`url`, `values`) => `Promise`\<`void`\>

Defined in: manageBridge.ts:26

Hands the proof to htmx to POST and swap the list partial.

#### Parameters

##### url

`string`

##### values

`Record`\<`string`, `unknown`\>

#### Returns

`Promise`\<`void`\>

***

### apiBase

> **apiBase**: `string`

Defined in: manageBridge.ts:20

Walletauth API base (for `manage/nonce/`).

***

### csrf

> **csrf**: `string`

Defined in: manageBridge.ts:18

CSRF token for the nonce POST.

***

### fetchFn

> **fetchFn**: \{(`input`, `init?`): `Promise`\<`Response`\>; (`input`, `init?`): `Promise`\<`Response`\>; \}

Defined in: manageBridge.ts:16

`fetch` implementation.

#### Call Signature

> (`input`, `init?`): `Promise`\<`Response`\>

[MDN Reference](https://developer.mozilla.org/docs/Web/API/Window/fetch)

##### Parameters

###### input

`URL` \| `RequestInfo`

###### init?

`RequestInit`

##### Returns

`Promise`\<`Response`\>

#### Call Signature

> (`input`, `init?`): `Promise`\<`Response`\>

[MDN Reference](https://developer.mozilla.org/docs/Web/API/Window/fetch)

##### Parameters

###### input

`string` \| `URL` \| `Request`

###### init?

`RequestInit`

##### Returns

`Promise`\<`Response`\>

***

### opsUrl

> **opsUrl**: `string`

Defined in: manageBridge.ts:22

Site URL that performs the operation and returns the refreshed list.

***

### stepUpSign

> **stepUpSign**: [`StepUpSigner`](../../manageAdapters/type-aliases/StepUpSigner.md)

Defined in: manageBridge.ts:24

Wallet step-up signer.
