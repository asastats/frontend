[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/links](../README.md) / handleLinkClick

# Function: handleLinkClick()

> **handleLinkClick**(`event`, `origin`, `navigate`): `boolean`

Defined in: [app/links.ts:44](https://github.com/asastats/frontend/blob/main/wallet/src/app/links.ts#L44)

Handle one click, if it is a plain tap on a link this module owns.

## Parameters

### event

`MouseEvent`

the click.

### origin

`string`

the site's origin.

### navigate

(`url`) => `void`

goes to a same-site URL in place.

## Returns

`boolean`

whether the click was taken over.
