[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/downloads](../README.md) / download

# Function: download()

> **download**(`url`, `init?`, `fallback?`, `host?`): `Promise`\<`boolean`\>

Defined in: [app/downloads.ts:115](https://github.com/asastats/frontend/blob/main/wallet/src/app/downloads.ts#L115)

Download `url` and share it; show the page instead if it is not a file.

## Parameters

### url

`string`

same-site URL.

### init?

`RequestInit` = `{}`

fetch options.

### fallback?

(`responseUrl`) => `void`

shows a non-file response the ordinary way.

### host?

`HTMLElement` \| `null`

where an error notice goes.

## Returns

`Promise`\<`boolean`\>

whether a file was shared.
