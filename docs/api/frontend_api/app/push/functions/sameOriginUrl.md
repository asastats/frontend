[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/push](../README.md) / sameOriginUrl

# Function: sameOriginUrl()

> **sameOriginUrl**(`href`, `origin`): `string` \| `null`

Defined in: [app/push.ts:179](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L179)

Return `href` if it is a page of this site, else null.

## Parameters

### href

`unknown`

from the notification's data.

### origin

`string`

the site's origin.

## Returns

`string` \| `null`

the absolute URL, or null.
