[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/returnPage](../README.md) / returnTarget

# Function: returnTarget()

> **returnTarget**(`location`, `storage`, `now`): `string` \| `null`

Defined in: [app/returnPage.ts:64](https://github.com/asastats/frontend/blob/main/wallet/src/app/returnPage.ts#L64)

Return the page to go back to, if this load is the app starting over.

Reads the remembered page once and drops it.

## Parameters

### location

`Pick`\<`Location`, `"search"` \| `"replace"` \| `"href"` \| `"origin"` \| `"pathname"`\>

where the WebView is now.

### storage

`Storage`

where the page is kept.

### now

`number`

the time, in ms.

## Returns

`string` \| `null`

a same-site URL, or null to stay.
