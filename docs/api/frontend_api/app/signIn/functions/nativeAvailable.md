[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/signIn](../README.md) / nativeAvailable

# Function: nativeAvailable()

> **nativeAvailable**(`provider`): `Promise`\<`boolean`\>

Defined in: [app/signIn.ts:163](https://github.com/asastats/frontend/blob/main/wallet/src/app/signIn.ts#L163)

Whether this phone has a native sheet for `provider`.

## Parameters

### provider

`string`

an allauth provider id.

## Returns

`Promise`\<`boolean`\>

false for other providers and for app versions without the plugin.
