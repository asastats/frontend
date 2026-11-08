[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/flutterAddresses](../README.md) / validEntries

# Function: validEntries()

> **validEntries**(`saved`): `string`[]

Defined in: [app/flutterAddresses.ts:33](https://github.com/asastats/frontend/blob/main/wallet/src/app/flutterAddresses.ts#L33)

Keep each saved search's addresses and .algo names; a search of several becomes
one bundle entry joined by commas, as index.js stores it.

## Parameters

### saved

`unknown`[]

entries as read.

## Returns

`string`[]

the valid entries, in order.
