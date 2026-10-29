[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/links](../README.md) / installLinks

# Function: installLinks()

> **installLinks**(`doc?`, `navigate?`): `void`

Defined in: [app/links.ts:77](https://github.com/asastats/frontend/blob/main/wallet/src/app/links.ts#L77)

Take over link taps on `doc`.

Bubble phase, so a page script that handles its own link first wins.

## Parameters

### doc?

`Document` = `document`

the document to listen on.

### navigate?

(`url`) => `void`

goes to a same-site URL in place.

## Returns

`void`
