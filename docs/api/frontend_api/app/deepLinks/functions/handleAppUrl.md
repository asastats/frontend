[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/deepLinks](../README.md) / handleAppUrl

# Function: handleAppUrl()

> **handleAppUrl**(`event`, `origin`, `navigate`): `boolean`

Defined in: [app/deepLinks.ts:15](https://github.com/asastats/frontend/blob/main/wallet/src/app/deepLinks.ts#L15)

Open `event.url` in the WebView if it is a page of this site.

## Parameters

### event

`URLOpenListenerEvent`

from the App plugin.

### origin

`string`

the site's origin.

### navigate

(`url`) => `void`

goes to the URL.

## Returns

`boolean`

whether the URL was followed.
