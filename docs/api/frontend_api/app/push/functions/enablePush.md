[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/push](../README.md) / enablePush

# Function: enablePush()

> **enablePush**(`urls`): `Promise`\<[`PushResult`](../interfaces/PushResult.md)\>

Defined in: [app/push.ts:119](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L119)

Ask permission, get the token and register it; remember the urls on success.

## Parameters

### urls

[`DeviceUrls`](../interfaces/DeviceUrls.md)

the device endpoints.

## Returns

`Promise`\<[`PushResult`](../interfaces/PushResult.md)\>

what happened, for the modal's state line.
