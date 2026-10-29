[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/downloads](../README.md) / attachmentName

# Function: attachmentName()

> **attachmentName**(`header`): `string` \| `null`

Defined in: [app/downloads.ts:35](https://github.com/asastats/frontend/blob/main/wallet/src/app/downloads.ts#L35)

Return the file name from a `Content-Disposition` header, or null when the
response is not an attachment.

## Parameters

### header

`string` \| `null`

the header value, possibly null.

## Returns

`string` \| `null`

a safe base name, or null.
