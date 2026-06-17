[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [manageBootstrap](../README.md) / initManageAddresses

# Function: initManageAddresses()

> **initManageAddresses**(`doc?`): `void`

Defined in: [manageBootstrap.ts:46](https://github.com/asastats/frontend/blob/main/wallet/src/manageBootstrap.ts#L46)

Wire the connected-addresses manager when its container is present.

Plain reducing actions (remove, disable-login) are declarative `hx-post`
buttons handled by htmx directly. Privilege-expanding actions carry
`data-stepup`; those are intercepted here to obtain a wallet signature before
htmx posts the proof. No-ops when the container is absent.

## Parameters

### doc?

`Document` = `document`

Document to query (defaults to the global document).

## Returns

`void`
