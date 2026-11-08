[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/statusBar](../README.md) / installStatusBar

# Function: installStatusBar()

> **installStatusBar**(`doc?`): `MutationObserver`

Defined in: [app/statusBar.ts:76](https://github.com/asastats/frontend/blob/main/wallet/src/app/statusBar.ts#L76)

Sync now, when theme.js switches the theme (`data-theme` on `<html>`), when
the page is shown again (Back restores it from the back-forward cache with no script rerun),
and when the phone switches light/dark: the default theme follows it with no `data-theme` change.

## Parameters

### doc?

`Document` = `document`

the document.

## Returns

`MutationObserver`

the observer, for tests.
