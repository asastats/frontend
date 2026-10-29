[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/downloads](../README.md) / blobToBase64

# Function: blobToBase64()

> **blobToBase64**(`blob`): `Promise`\<`string`\>

Defined in: [app/downloads.ts:78](https://github.com/asastats/frontend/blob/main/wallet/src/app/downloads.ts#L78)

Return `blob` as base64, the form `Filesystem.writeFile` takes.

## Parameters

### blob

`Blob`

file contents.

## Returns

`Promise`\<`string`\>

base64 without a data-URL prefix.
