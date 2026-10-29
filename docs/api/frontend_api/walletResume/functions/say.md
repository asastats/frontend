[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / say

# Function: say()

> **say**(`doc`, `wallet`, `text`): `HTMLElement` \| `null`

Defined in: [walletResume.ts:538](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L538)

Put `text` in the wallet card's notice (the one `app/walletHandoff.ts` shows), or a new one.

## Parameters

### doc

`Document`

the page.

### wallet

`string`

wallet id.

### text

`string`

what to say.

## Returns

`HTMLElement` \| `null`

the notice, or null without the card.
