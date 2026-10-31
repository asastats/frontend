[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/flutterAddresses](../README.md) / mergeEntries

# Function: mergeEntries()

> **mergeEntries**(`own`, `flutter`): `string`[]

Defined in: [app/flutterAddresses.ts:45](https://github.com/asastats/frontend/blob/main/wallet/src/app/flutterAddresses.ts#L45)

The app's own entries first (they are newer), then Flutter's; no repeats, capped.

## Parameters

### own

`string`[]

what the list holds now.

### flutter

`string`[]

what the Flutter app saved.

## Returns

`string`[]

the merged list.
