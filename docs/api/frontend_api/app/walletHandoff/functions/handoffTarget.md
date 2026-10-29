[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/walletHandoff](../README.md) / handoffTarget

# Function: handoffTarget()

> **handoffTarget**(`storage`, `session`, `origin`, `now`): [`HandoffWallet`](../interfaces/HandoffWallet.md) & `object` \| `null`

Defined in: [app/walletHandoff.ts:106](https://github.com/asastats/frontend/blob/main/wallet/src/app/walletHandoff.ts#L106)

Return the interrupted hand-off, if this load is the app starting over.

Reads the noted hand-off once and drops it; marks this WebView as alive.

## Parameters

### storage

`Storage`

localStorage.

### session

`Storage`

sessionStorage, which a restart empties.

### origin

`string`

this site's origin.

### now

`number`

the time, in ms.

## Returns

[`HandoffWallet`](../interfaces/HandoffWallet.md) & `object` \| `null`

the wallet and the page to go back to, or null.
