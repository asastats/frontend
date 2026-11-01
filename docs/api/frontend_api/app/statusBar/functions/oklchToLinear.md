[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/statusBar](../README.md) / oklchToLinear

# Function: oklchToLinear()

> **oklchToLinear**(`color`): \[`number`, `number`, `number`\] \| `null`

Defined in: [app/statusBar.ts:17](https://github.com/asastats/frontend/blob/main/wallet/src/app/statusBar.ts#L17)

Linear sRGB of an `oklch(L C H)` colour, clamped to the sRGB gamut.

## Parameters

### color

`string`

a computed colour; WebKit and Chrome return daisyUI themes in oklch.

## Returns

\[`number`, `number`, `number`\] \| `null`

[r, g, b] in 0..1, or null when it is not oklch.
