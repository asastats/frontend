[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [manageAddressesComponent](../README.md) / ManageAddressesComponent

# Class: ManageAddressesComponent

Defined in: [manageAddressesComponent.ts:61](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L61)

Drives the connected-addresses management page: lists the caller's addresses
and performs set-primary / remove / login-toggle / add-address against the
walletauth endpoints. Privilege-expanding actions (make primary, enable
login) obtain a step-up challenge and sign it with the current primary; the
wallet interactions are injected, so the orchestration is fully testable.

## Constructors

### Constructor

> **new ManageAddressesComponent**(`element`, `apiBase?`, `deps`): `ManageAddressesComponent`

Defined in: [manageAddressesComponent.ts:72](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L72)

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

Defined in: [manageAddressesComponent.ts:63](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L63)

***

### deps

> `private` **deps**: [`ManageDeps`](../interfaces/ManageDeps.md)

Defined in: [manageAddressesComponent.ts:64](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L64)

***

### element

> `private` **element**: `HTMLElement`

Defined in: [manageAddressesComponent.ts:62](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L62)

***

### rows

> `private` **rows**: [`AddressRow`](../interfaces/AddressRow.md)[] = `[]`

Defined in: [manageAddressesComponent.ts:65](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L65)

## Accessors

### fetchFn

#### Get Signature

> **get** `private` **fetchFn**(): \{(`input`, `init?`): `Promise`\<`Response`\>; (`input`, `init?`): `Promise`\<`Response`\>; \}

Defined in: [manageAddressesComponent.ts:88](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L88)

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

Defined in: [manageAddressesComponent.ts:247](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L247)

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

Defined in: [manageAddressesComponent.ts:258](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L258)

Delegate clicks on action buttons (including the static "add" button).

#### Returns

`void`

***

### bind()

> **bind**(): `Promise`\<`void`\>

Defined in: [manageAddressesComponent.ts:83](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L83)

Wire click delegation and load the current address list.

#### Returns

`Promise`\<`void`\>

***

### getCsrfToken()

> `private` **getCsrfToken**(): `string`

Defined in: [manageAddressesComponent.ts:94](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L94)

CSRF token from cookie, falling back to a hidden input.

#### Returns

`string`

***

### handle()

> `private` **handle**(`action`, `id`): `Promise`\<`void`\>

Defined in: [manageAddressesComponent.ts:276](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L276)

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

Defined in: [manageAddressesComponent.ts:108](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L108)

#### Returns

`Record`\<`string`, `string`\>

***

### initCollapsible()

> `private` **initCollapsible**(`ul`): `void`

Defined in: [manageAddressesComponent.ts:231](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L231)

#### Parameters

##### ul

`HTMLElement`

#### Returns

`void`

***

### load()

> **load**(): `Promise`\<`void`\>

Defined in: [manageAddressesComponent.ts:130](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L130)

Fetch the caller's addresses and render them.

#### Returns

`Promise`\<`void`\>

***

### messageOf()

> `private` **messageOf**(`error`): `string`

Defined in: [manageAddressesComponent.ts:339](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L339)

#### Parameters

##### error

`unknown`

#### Returns

`string`

***

### post()

> `private` **post**(`body`): `Promise`\<`void`\>

Defined in: [manageAddressesComponent.ts:298](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L298)

POST a non-step-up management operation; throws on a failed result.

#### Parameters

##### body

`Record`\<`string`, `unknown`\>

#### Returns

`Promise`\<`void`\>

***

### render()

> `private` **render**(): `void`

Defined in: [manageAddressesComponent.ts:149](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L149)

Render the addresses as a Materialize collapsible: one `<li>` per address,
the address in its `collapsible-header` and that address's actions tucked
into the `collapsible-body`. The primary row's body shows a note instead of
actions (it has none).

#### Returns

`void`

***

### showError()

> `private` **showError**(`message`): `void`

Defined in: [manageAddressesComponent.ts:116](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L116)

Surface an error via a Materialize toast, or a card panel fallback.

#### Parameters

##### message

`string`

#### Returns

`void`

***

### stepUp()

> `private` **stepUp**(`body`): `Promise`\<`void`\>

Defined in: [manageAddressesComponent.ts:316](https://github.com/asastats/frontend/blob/main/frontend/src/manageAddressesComponent.ts#L316)

Perform a step-up operation: fetch a challenge bound to the current
primary, sign it with that wallet, then POST the operation with the proof.

#### Parameters

##### body

`Record`\<`string`, `unknown`\>

The operation payload (operation, target_id, extras).

#### Returns

`Promise`\<`void`\>
