[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/downloads](../README.md) / fetchFile

# Function: fetchFile()

> **fetchFile**(`url`, `init?`): `Promise`\<\{ `file`: [`DownloadedFile`](../interfaces/DownloadedFile.md) \| `null`; `responseUrl`: `string`; \}\>

Defined in: [app/downloads.ts:61](https://github.com/asastats/frontend/blob/main/wallet/src/app/downloads.ts#L61)

Fetch `url` and return the file it answers with, or null if it is not one.

## Parameters

### url

`string`

same-site URL.

### init?

`RequestInit` = `{}`

fetch options (method, body).

## Returns

`Promise`\<\{ `file`: [`DownloadedFile`](../interfaces/DownloadedFile.md) \| `null`; `responseUrl`: `string`; \}\>

the file, or null with the response URL to show instead.
