[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [notify](../README.md) / NotifyDetail

# Interface: NotifyDetail

Defined in: [notify.ts:26](https://github.com/asastats/frontend/blob/main/wallet/src/notify.ts#L26)

Payload carried by [NOTIFY\_EVENT](../variables/NOTIFY_EVENT.md).

## Properties

### level

> **level**: [`NoticeLevel`](../type-aliases/NoticeLevel.md)

Defined in: [notify.ts:30](https://github.com/asastats/frontend/blob/main/wallet/src/notify.ts#L30)

Severity, for hosts that style by level.

***

### message

> **message**: `string`

Defined in: [notify.ts:28](https://github.com/asastats/frontend/blob/main/wallet/src/notify.ts#L28)

Human-readable text. Treated as untrusted: hosts must not parse it as markup.
