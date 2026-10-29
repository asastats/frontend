[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/push](../README.md) / FirebaseMessagingPlugin

# Interface: FirebaseMessagingPlugin

Defined in: [app/push.ts:30](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L30)

The part of `@capacitor-firebase/messaging` this module calls.

Declared here rather than imported: that package's web half imports the
Firebase SDK, which `app.js` must not pull in. See docs/logbook.md.

## Methods

### addListener()

#### Call Signature

> **addListener**(`eventName`, `listener`): `Promise`\<`PluginListenerHandle`\>

Defined in: [app/push.ts:35](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L35)

##### Parameters

###### eventName

`"tokenReceived"`

###### listener

(`event`) => `void`

##### Returns

`Promise`\<`PluginListenerHandle`\>

#### Call Signature

> **addListener**(`eventName`, `listener`): `Promise`\<`PluginListenerHandle`\>

Defined in: [app/push.ts:39](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L39)

##### Parameters

###### eventName

`"notificationActionPerformed"`

###### listener

(`event`) => `void`

##### Returns

`Promise`\<`PluginListenerHandle`\>

***

### checkPermissions()

> **checkPermissions**(): `Promise`\<\{ `receive`: `string`; \}\>

Defined in: [app/push.ts:31](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L31)

#### Returns

`Promise`\<\{ `receive`: `string`; \}\>

***

### deleteToken()

> **deleteToken**(): `Promise`\<`void`\>

Defined in: [app/push.ts:34](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L34)

#### Returns

`Promise`\<`void`\>

***

### getToken()

> **getToken**(): `Promise`\<\{ `token`: `string`; \}\>

Defined in: [app/push.ts:33](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L33)

#### Returns

`Promise`\<\{ `token`: `string`; \}\>

***

### requestPermissions()

> **requestPermissions**(): `Promise`\<\{ `receive`: `string`; \}\>

Defined in: [app/push.ts:32](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L32)

#### Returns

`Promise`\<\{ `receive`: `string`; \}\>
