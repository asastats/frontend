[**asastats-wallet-frontend**](../../README.md)

***

[asastats-wallet-frontend](../../README.md) / [ManageAddressesComponent](../README.md) / ManageAddressesComponent

# Class: ManageAddressesComponent

Defined in: [ManageAddressesComponent.ts:61](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L61)

Drives the connected-addresses management page: lists the caller's addresses
and performs set-primary / remove / login-toggle / add-address against the
walletauth endpoints. Privilege-expanding actions (make primary, enable
login) obtain a step-up challenge and sign it with the current primary; the
wallet interactions are injected, so the orchestration is fully testable.

## Constructors

### Constructor

> **new ManageAddressesComponent**(`element`, `apiBase?`, `deps`): `ManageAddressesComponent`

Defined in: [ManageAddressesComponent.ts:72](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L72)

#### Parameters

##### element

`HTMLElement`

Container (`#connected-addresses`).

##### apiBase?

`string` = `DEFAULT_MANAGE_API_BASE`

walletauth API base (default `/api/v2/wallet`).

##### deps

[`ManageDeps`](../interfaces/ManageDeps.md)

Injected fetch / signer / add-address collaborators.

#### Returns

`ManageAddressesComponent`

## Properties

### apiBase

> `private` **apiBase**: `string`

Defined in: [ManageAddressesComponent.ts:63](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L63)

***

### deps

> `private` **deps**: [`ManageDeps`](../interfaces/ManageDeps.md)

Defined in: [ManageAddressesComponent.ts:64](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L64)

***

### element

> `private` **element**: `HTMLElement`

Defined in: [ManageAddressesComponent.ts:62](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L62)

***

### rows

> `private` **rows**: [`AddressRow`](../interfaces/AddressRow.md)[] = `[]`

Defined in: [ManageAddressesComponent.ts:65](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L65)

## Accessors

### fetchFn

#### Get Signature

> **get** `private` **fetchFn**(): \{(`input`, `init?`): `Promise`\<`Response`\>; (`input`, `init?`): `Promise`\<`Response`\>; \}

Defined in: [ManageAddressesComponent.ts:88](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L88)

##### Returns

> (`input`, `init?`): `Promise`\<`Response`\>

[MDN Reference](https://developer.mozilla.org/docs/Web/API/Window/fetch)

###### Parameters

###### input

`URL` \| `RequestInfo`

###### init?

`RequestInit`

###### Returns

`Promise`\<`Response`\>

> (`input`, `init?`): `Promise`\<`Response`\>

[MDN Reference](https://developer.mozilla.org/docs/Web/API/Window/fetch)

###### Parameters

###### input

`string` \| `URL` \| `Request`

###### init?

`RequestInit`

###### Returns

`Promise`\<`Response`\>

## Methods

### actionButton()

> `private` **actionButton**(`label`, `action`, `id`): `HTMLButtonElement`

Defined in: [ManageAddressesComponent.ts:173](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L173)

#### Parameters

##### label

`string`

##### action

`string`

##### id

`number`

#### Returns

`HTMLButtonElement`

***

### addEventListeners()

> `private` **addEventListeners**(): `void`

Defined in: [ManageAddressesComponent.ts:184](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L184)

Delegate clicks on action buttons (including the static "add" button).

#### Returns

`void`

***

### bind()

> **bind**(): `Promise`\<`void`\>

Defined in: [ManageAddressesComponent.ts:83](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L83)

Wire click delegation and load the current address list.

#### Returns

`Promise`\<`void`\>

***

### getCsrfToken()

> `private` **getCsrfToken**(): `string`

Defined in: [ManageAddressesComponent.ts:94](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L94)

CSRF token from cookie, falling back to a hidden input.

#### Returns

`string`

***

### handle()

> `private` **handle**(`action`, `id`): `Promise`\<`void`\>

Defined in: [ManageAddressesComponent.ts:202](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L202)

Route an action to its handler with shared error reporting and reload.

#### Parameters

##### action

`string`

The data-action of the clicked button.

##### id

`number`

The target address id (NaN for "add").

#### Returns

`Promise`\<`void`\>

***

### headers()

> `private` **headers**(): `Record`\<`string`, `string`\>

Defined in: [ManageAddressesComponent.ts:108](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L108)

#### Returns

`Record`\<`string`, `string`\>

***

### load()

> **load**(): `Promise`\<`void`\>

Defined in: [ManageAddressesComponent.ts:130](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L130)

Fetch the caller's addresses and render them.

#### Returns

`Promise`\<`void`\>

***

### messageOf()

> `private` **messageOf**(`error`): `string`

Defined in: [ManageAddressesComponent.ts:265](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L265)

#### Parameters

##### error

`unknown`

#### Returns

`string`

***

### post()

> `private` **post**(`body`): `Promise`\<`void`\>

Defined in: [ManageAddressesComponent.ts:224](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L224)

POST a non-step-up management operation; throws on a failed result.

#### Parameters

##### body

`Record`\<`string`, `unknown`\>

#### Returns

`Promise`\<`void`\>

***

### render()

> `private` **render**(): `void`

Defined in: [ManageAddressesComponent.ts:144](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L144)

Render one row per address with the actions allowed for it.

#### Returns

`void`

***

### showError()

> `private` **showError**(`message`): `void`

Defined in: [ManageAddressesComponent.ts:116](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L116)

Surface an error via a Materialize toast, or a card panel fallback.

#### Parameters

##### message

`string`

#### Returns

`void`

***

### stepUp()

> `private` **stepUp**(`body`): `Promise`\<`void`\>

Defined in: [ManageAddressesComponent.ts:242](https://github.com/asastats/frontend/blob/main/frontend/src/ManageAddressesComponent.ts#L242)

Perform a step-up operation: fetch a challenge bound to the current
primary, sign it with that wallet, then POST the operation with the proof.

#### Parameters

##### body

`Record`\<`string`, `unknown`\>

The operation payload (operation, target_id, extras).

#### Returns

`Promise`\<`void`\>
