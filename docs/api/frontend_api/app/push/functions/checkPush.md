[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/push](../README.md) / checkPush

# Function: checkPush()

> **checkPush**(`urls`): `Promise`\<`boolean`\>

Defined in: [app/push.ts:141](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L141)

Re-register silently a device the reader turned on; never prompts.

Android before 13 grants the permission at install, so a granted
permission alone is not the reader's consent.

## Parameters

### urls

[`DeviceUrls`](../interfaces/DeviceUrls.md)

the device endpoints.

## Returns

`Promise`\<`boolean`\>

whether this device is on.
