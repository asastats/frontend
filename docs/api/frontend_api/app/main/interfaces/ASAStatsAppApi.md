[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/main](../README.md) / ASAStatsAppApi

# Interface: ASAStatsAppApi

Defined in: [app/main.ts:23](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L23)

The global page scripts feature-detect; see capacitor/HANDOFF.md §6.

## Properties

### checkPush

> **checkPush**: (`urls`) => `Promise`\<`boolean`\>

Defined in: [app/main.ts:30](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L30)

Re-register without prompting; whether this device is on.

#### Parameters

##### urls

[`DeviceUrls`](../../push/interfaces/DeviceUrls.md)

#### Returns

`Promise`\<`boolean`\>

***

### disablePush

> **disablePush**: () => `Promise`\<`void`\>

Defined in: [app/main.ts:32](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L32)

Unregister this device; done before logout.

#### Returns

`Promise`\<`void`\>

***

### download

> **download**: (`url`) => `Promise`\<`boolean`\>

Defined in: [app/main.ts:26](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L26)

Fetch a same-site file and open the share sheet for it.

#### Parameters

##### url

`string`

#### Returns

`Promise`\<`boolean`\>

***

### enablePush

> **enablePush**: (`urls`) => `Promise`\<[`PushResult`](../../push/interfaces/PushResult.md)\>

Defined in: [app/main.ts:28](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L28)

Ask permission and register this device for alerts (widgets `alerts.js`).

#### Parameters

##### urls

[`DeviceUrls`](../../push/interfaces/DeviceUrls.md)

#### Returns

`Promise`\<[`PushResult`](../../push/interfaces/PushResult.md)\>

***

### isApp

> **isApp**: `true`

Defined in: [app/main.ts:24](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L24)

***

### signIn

> **signIn**: (`provider`, `next?`) => `Promise`\<`boolean`\>

Defined in: [app/main.ts:34](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L34)

Social sign-in through the system browser (F4); whether it was sent.

#### Parameters

##### provider

`string`

##### next?

`string`

#### Returns

`Promise`\<`boolean`\>
