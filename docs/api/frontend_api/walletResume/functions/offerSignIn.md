[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / offerSignIn

# Function: offerSignIn()

> **offerSignIn**(`doc`, `step`, `signed`, `csrf`, `go?`): `HTMLElement` \| `null`

Defined in: [walletResume.ts:562](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L562)

Ask before using a collected signature to sign in (R5), then post it.

## Parameters

### doc

`Document`

the page.

### step

[`SignStep`](../interfaces/SignStep.md)

the sign step.

### signed

`string`

the signed proof, base64; never stored (R3).

### csrf

`string`

the CSRF token.

### go?

(`url`) => `void`

follows the server's redirect.

## Returns

`HTMLElement` \| `null`

the notice holding the question, or null without the card.
