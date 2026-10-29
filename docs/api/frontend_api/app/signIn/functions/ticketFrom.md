[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/signIn](../README.md) / ticketFrom

# Function: ticketFrom()

> **ticketFrom**(`url`, `origin`): `string` \| `null`

Defined in: [app/signIn.ts:112](https://github.com/asastats/frontend/blob/main/wallet/src/app/signIn.ts#L112)

Return the ticket from the sheet's callback URL, if it is ours.

## Parameters

### url

`string`

what the plugin returned.

### origin

`string`

this site's origin.

## Returns

`string` \| `null`

the ticket, or null.
