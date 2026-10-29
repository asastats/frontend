[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/push](../README.md) / register

# Function: register()

> **register**(`urls`, `token`): `Promise`\<`boolean`\>

Defined in: [app/push.ts:108](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L108)

Send this device's token to the server.

## Parameters

### urls

[`DeviceUrls`](../interfaces/DeviceUrls.md)

the device endpoints.

### token

`string`

the FCM registration token.

## Returns

`Promise`\<`boolean`\>

whether it was stored.
