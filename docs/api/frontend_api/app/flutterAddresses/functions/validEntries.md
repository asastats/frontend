[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/flutterAddresses](../README.md) / validEntries

# Function: validEntries()

> **validEntries**(`saved`): `string`[]

Defined in: [app/flutterAddresses.ts:31](https://github.com/asastats/frontend/blob/main/wallet/src/app/flutterAddresses.ts#L31)

Split saved entries (Flutter kept a multi-address search as one string) and keep
the addresses and .algo names.

## Parameters

### saved

`unknown`[]

entries as read.

## Returns

`string`[]

the valid entries, in order.
