[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/main](../README.md) / start

# Function: start()

> **start**(): `boolean`

Defined in: [app/main.ts:71](https://github.com/asastats/frontend/blob/main/wallet/src/app/main.ts#L71)

Wire every native behaviour, if the native bridge is present.

The user-agent token alone put this page in app mode; without the bridge
(an old shell, a browser faking the token) the plugins would only reject.

## Returns

`boolean`

whether the bridge was found.
