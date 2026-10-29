[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/push](../README.md) / disablePush

# Function: disablePush()

> **disablePush**(): `Promise`\<`void`\>

Defined in: [app/push.ts:159](https://github.com/asastats/frontend/blob/main/wallet/src/app/push.ts#L159)

Remove this device from the account and drop its token. Never throws: a
logout must go ahead even offline (the server re-homes the token anyway).

## Returns

`Promise`\<`void`\>
