[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [manageAddressesComponent](../README.md) / ManageDeps

# Interface: ManageDeps

Defined in: [manageAddressesComponent.ts:36](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L36)

Injected collaborators; the wallet-touching ones are browser-only adapters.

## Properties

### addAddress

> **addAddress**: (`apiBase`) => `Promise`\<`void`\>

Defined in: [manageAddressesComponent.ts:51](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L51)

Run the full "add address" link flow against `apiBase`.

#### Parameters

##### apiBase

`string`

#### Returns

`Promise`\<`void`\>

***

### fetchFn?

> `optional` **fetchFn?**: \{(`input`, `init?`): `Promise`\<`Response`\>; (`input`, `init?`): `Promise`\<`Response`\>; \}

Defined in: [manageAddressesComponent.ts:38](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L38)

`fetch` implementation (defaults to the global).

#### Call Signature

> (`input`, `init?`): `Promise`\<`Response`\>

[MDN Reference](https://developer.mozilla.org/docs/Web/API/Window/fetch)

##### Parameters

###### input

`URL` \| `RequestInfo`

###### init?

`RequestInit`

##### Returns

`Promise`\<`Response`\>

#### Call Signature

> (`input`, `init?`): `Promise`\<`Response`\>

[MDN Reference](https://developer.mozilla.org/docs/Web/API/Window/fetch)

##### Parameters

###### input

`string` \| `URL` \| `Request`

###### init?

`RequestInit`

##### Returns

`Promise`\<`Response`\>

***

### stepUpSign

> **stepUpSign**: (`address`, `chain`, `message`) => `Promise`\<`Record`\<`string`, `unknown`\>\>

Defined in: [manageAddressesComponent.ts:45](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L45)

Sign `message` with the wallet holding `address` on `chain` (step-up).
Resolves to the payload fragment to merge into the verify POST (e.g.
`{ signature }` for EVM). Must reject if the connected account is not
`address`, so step-up can only be satisfied by the real primary key.

#### Parameters

##### address

`string`

##### chain

`string`

##### message

`string`

#### Returns

`Promise`\<`Record`\<`string`, `unknown`\>\>
