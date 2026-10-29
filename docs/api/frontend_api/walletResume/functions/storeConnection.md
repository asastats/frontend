[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [walletResume](../README.md) / storeConnection

# Function: storeConnection()

> **storeConnection**(`step`, `approval`, `storage`): `void`

Defined in: [walletResume.ts:449](https://github.com/asastats/frontend/blob/main/wallet/src/walletResume.ts#L449)

Store a connect the wallet approved where its library and use-wallet read it back.

## Parameters

### step

[`ConnectStep`](../interfaces/ConnectStep.md)

the connect.

### approval

from [acceptApproval](acceptApproval.md).

#### accounts

`string`[]

#### chainId

`number`

#### peerId

`string`

#### peerMeta

`unknown`

### storage

`Storage`

localStorage.

## Returns

`void`
