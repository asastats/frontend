[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/downloads](../README.md) / installDownloads

# Function: installDownloads()

> **installDownloads**(`doc?`): `void`

Defined in: [app/downloads.ts:145](https://github.com/asastats/frontend/blob/main/wallet/src/app/downloads.ts#L145)

Take over taps on `a[data-app-download]`, and submits of a
`form[data-app-download]` or through a submit button carrying it.

A form whose response is not a file is submitted again natively, so the
server's own page (validation errors, messages) shows as it would in a
browser.

## Parameters

### doc?

`Document` = `document`

the document to listen on.

## Returns

`void`
