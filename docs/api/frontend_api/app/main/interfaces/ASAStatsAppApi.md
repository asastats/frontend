[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/main](../README.md) / ASAStatsAppApi

# Interface: ASAStatsAppApi

Defined in: [app/main.ts:24](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L24)

The global page scripts feature-detect; see capacitor/HANDOFF.md §6.

## Properties

### checkPush

> **checkPush**: (`urls`) => `Promise`\<`boolean`\>

Defined in: [app/main.ts:31](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L31)

Re-register without prompting; whether this device is on.

#### Parameters

##### urls

[`DeviceUrls`](../../push/interfaces/DeviceUrls.md)

#### Returns

`Promise`\<`boolean`\>

***

### disablePush

> **disablePush**: () => `Promise`\<`void`\>

Defined in: [app/main.ts:33](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L33)

Unregister this device; done before logout.

#### Returns

`Promise`\<`void`\>

***

### download

> **download**: (`url`) => `Promise`\<`boolean`\>

Defined in: [app/main.ts:27](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L27)

Fetch a same-site file and open the share sheet for it.

#### Parameters

##### url

`string`

#### Returns

`Promise`\<`boolean`\>

***

### enablePush

> **enablePush**: (`urls`) => `Promise`\<[`PushResult`](../../push/interfaces/PushResult.md)\>

Defined in: [app/main.ts:29](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L29)

Ask permission and register this device for alerts (widgets `alerts.js`).

#### Parameters

##### urls

[`DeviceUrls`](../../push/interfaces/DeviceUrls.md)

#### Returns

`Promise`\<[`PushResult`](../../push/interfaces/PushResult.md)\>

***

### isApp

> **isApp**: `true`

Defined in: [app/main.ts:25](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L25)

***

### signIn

> **signIn**: (`provider`, `next?`) => `Promise`\<`boolean`\>

Defined in: [app/main.ts:35](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L35)

Social sign-in through the system browser (F4); whether it was sent.

#### Parameters

##### provider

`string`

##### next?

`string`

#### Returns

`Promise`\<`boolean`\>
