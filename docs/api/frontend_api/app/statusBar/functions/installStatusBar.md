[**wallet-frontend**](../../../README.md)

***

[wallet-frontend](../../../README.md) / [app/statusBar](../README.md) / installStatusBar

# Function: installStatusBar()

> **installStatusBar**(`doc?`): `MutationObserver`

Defined in: [app/statusBar.ts:75](https://github.com/asastats/frontend/blob/main/wallet/src/app/statusBar.ts#L75)

Sync now, when theme.js switches the theme (`data-theme` on `<html>`), and when
the page is shown again: Back restores it from the back-forward cache with no script rerun.

## Parameters

### doc?

`Document` = `document`

the document.

## Returns

`MutationObserver`

the observer, for tests.
