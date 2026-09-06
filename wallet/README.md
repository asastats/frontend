# Wallet package

A TypeScript application, built with Vite, that provides the browser-side wallet
experience: connecting a wallet, proving ownership of an address to the Django
backend, expanding privileges on the manage page, and signing swap groups.

This directory is `wallet/` at the repository root — not under `website/`,
because it is bundled rather than served from Django's static files.

The reference copy of this document is `docs/frontend.rst`, which Sphinx builds
along with the TypeDoc output in `docs/api/frontend_api/`. Keep the two in step.

## Overview

It uses [`@txnlab/use-wallet`](https://github.com/TxnLab/use-wallet) for Algorand
wallet management and an EIP-1193/EIP-6963 path of its own for EVM wallets, and
it talks to the Django backend over `/api/v2/wallet`.

## Architecture

Each concern is a module with one job, and the modules split three ways:

* **Components** own a wallet and its UI.
* **Bridges** are pure orchestration — no DOM, no network setup — so the flow
  they describe can be tested without a browser.
* **Bootstraps** are the browser-only wiring that finds the page's elements,
  reads CSRF, and hands a component to a bridge.

That split is why the suite can cover the logic without driving a wallet.

## Modules

| file | what it is |
| --- | --- |
| `main.ts` | entry point for the authorize page: fetches wallet and network data, binds the components, resumes a session, cleans up on unload |
| `walletComponent.ts` | one Algorand wallet's connection and the address-authorization flow; each wallet is its own card driven by its own instance |
| `evmWalletComponent.ts` | the EVM equivalent, mounted against `/api/v2/wallet/login` |
| `evmConnectors.ts` | browser-only adapters producing concrete connectors: EIP-6963 injected wallets, and WalletConnect |
| `evmBootstrap.ts` | wires the EVM flow to the page |
| `manageAdapters.ts` | step-up signing: signs a message with the wallet holding a given address on a given chain |
| `manageBridge.ts` | runs the privilege-expanding action requested from the manage page |
| `manageBootstrap.ts` | browser wiring for the manage page, including CSRF |
| `swapBootstrap.ts` | opt-in handling, partial-group signing, the wallet manager |
| `swapBridge.ts` | pure orchestration of a prepared swap: sign, submit, wait for confirmation |
| `notify.ts` | framework-free notification seam |
| `walletTestHarness.ts` | **test-only** mock wallet, in `src/` because the tests drive it as one |

## Development

```bash
cd wallet
npm install          # npm ci in CI
npm run dev          # Vite dev server
npm run build        # tsc && vite build
npm run build:docs   # regenerate ../docs/api/frontend_api/ with TypeDoc
```

## Testing

```bash
npm run test          # jest, via jest.config.cjs
npm run test:watch
npm run test:coverage
```

**Coverage is enforced**, not merely reported: `jest.config.cjs` sets a 100%
threshold on statements, branches, functions and lines. Exactly two things are
excluded, and both because they cannot be covered rather than because covering
them is awkward — `*.d.ts`, which has no runtime statements, and
`setupTests.ts`, which Jest loads before instrumentation. Everything else in
`src/` counts, the bootstraps and the test harness included.

## Wallet integration

Algorand wallets through `@txnlab/use-wallet`: Pera (mobile and web), Defly
(mobile), Lute (browser extension), and the other adapters the library
supports.

EVM wallets through this package's own connectors: EIP-6963 injected providers,
and WalletConnect via Reown. `WALLET_CONNECT_PROJECT_ID` in `website/.env` is
what enables the second; with it empty, only browser extensions work.

## Authentication flow

1. the reader connects a wallet
2. the app fetches a nonce from the backend
3. the reader signs it with the wallet
4. the backend verifies the signature
5. the address is authorized, and the reader is redirected

## Transaction types

* **Payment** — for authentication
* **Application call** — smart contract interactions
* **Asset transfer** — reward token claims, and swap legs
* **Atomic group** — swaps and other multi-transaction operations
