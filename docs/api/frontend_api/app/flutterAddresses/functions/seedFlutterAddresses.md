[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/flutterAddresses](../README.md) / seedFlutterAddresses

# Function: seedFlutterAddresses()

> **seedFlutterAddresses**(`storage?`): `Promise`\<`boolean`\>

Defined in: [app/flutterAddresses.ts:69](https://github.com/asastats/frontend/blob/main/wallet/src/app/flutterAddresses.ts#L69)

Merge the Flutter app's addresses into the list once, if the shell can read them.

A shell without the plugin, or a failed read, leaves the flag unset so a later
start tries again.

## Parameters

### storage?

`Storage` = `window.localStorage`

where the list lives.

## Returns

`Promise`\<`boolean`\>

whether the list was seeded on this call.
