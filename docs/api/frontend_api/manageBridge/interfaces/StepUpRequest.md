[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [manageBridge](../README.md) / StepUpRequest

# Interface: StepUpRequest

Defined in: manageBridge.ts:4

A privilege-expanding action requested from the manage page.

## Properties

### enabled?

> `optional` **enabled?**: `boolean`

Defined in: manageBridge.ts:10

For "set_login": the desired state (only `true` reaches step-up).

***

### operation

> **operation**: `string`

Defined in: manageBridge.ts:6

"set_primary" or "set_login".

***

### targetId

> **targetId**: `number`

Defined in: manageBridge.ts:8

The caller's own row the action targets.
