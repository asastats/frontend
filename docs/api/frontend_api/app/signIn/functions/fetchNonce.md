[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/signIn](../README.md) / fetchNonce

# Function: fetchNonce()

> **fetchNonce**(): `Promise`\<\{ `google_client_id`: `string`; `nonce`: `string`; \}\>

Defined in: [app/signIn.ts:177](https://github.com/asastats/frontend/blob/main/wallet/src/app/signIn.ts#L177)

Ask the server for this session's single-use nonce.

## Returns

`Promise`\<\{ `google_client_id`: `string`; `nonce`: `string`; \}\>

the nonce and the website's Google client id.
