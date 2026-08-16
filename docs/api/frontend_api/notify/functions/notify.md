[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [notify](../README.md) / notify

# Function: notify()

> **notify**(`host`, `message`, `level?`): `boolean`

Defined in: [notify.ts:46](https://github.com/asastats/frontend/blob/main/wallet/src/notify.ts#L46)

Surface a message to the user.

## Parameters

### host

`HTMLElement` \| `null`

Element the fallback notice is appended to, and the event's
  dispatch target so it bubbles through the component's own subtree. Pass
  `null` for callers with no container: the event still fires on `document`,
  but there is nowhere to place a fallback, so an unhandled message is
  dropped rather than appended to the page body.

### message

`string`

Text to show. Always rendered via `textContent`.

### level?

[`NoticeLevel`](../type-aliases/NoticeLevel.md) = `"error"`

Severity; defaults to `"error"`, which is what every current
  caller reports.

## Returns

`boolean`

Whether a host claimed the message.
