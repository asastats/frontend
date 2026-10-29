[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/links](../README.md) / classifyLink

# Function: classifyLink()

> **classifyLink**(`anchor`, `origin`): [`LinkAction`](../type-aliases/LinkAction.md)

Defined in: [app/links.ts:24](https://github.com/asastats/frontend/blob/main/wallet/src/app/links.ts#L24)

Decide what a tap on `anchor` should do.

## Parameters

### anchor

`HTMLAnchorElement`

the tapped link.

### origin

`string`

the site's origin, e.g. `https://www.asastats.com`.

## Returns

[`LinkAction`](../type-aliases/LinkAction.md)

the action.
