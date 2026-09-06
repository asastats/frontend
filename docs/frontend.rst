Wallet package
==============

A TypeScript application, built with Vite, that provides the browser-side wallet
experience: connecting a wallet, proving ownership of an address to the Django
backend, expanding privileges on the manage page, and signing swap groups.

It lives in **``wallet/``** at the repository root --- not under ``website/``,
because it is bundled rather than served from Django's static files, and not in
a directory called ``frontend``, which is the repository itself.

Overview
--------

It uses ``@txnlab/use-wallet`` for Algorand wallet management and an
EIP-1193/EIP-6963 path of its own for EVM wallets, and it talks to the Django
backend over ``/api/v2/wallet``.

Architecture
------------

Each concern is a module with one job, and the modules split three ways:

**Components** own a wallet and its UI. **Bridges** are pure orchestration ---
no DOM, no network setup --- so the flow they describe can be tested without a
browser. **Bootstraps** are the browser-only wiring that finds the page's
elements, reads CSRF, and hands a component to a bridge. That split is why the
suite can cover the logic without driving a wallet.

Main components
---------------

.. toctree::
   :maxdepth: 2

   api/frontend_api/main/classes/App.md
   api/frontend_api/walletComponent/classes/WalletComponent.md
   api/frontend_api/evmWalletComponent/classes/EvmWalletComponent.md

``main.ts``
~~~~~~~~~~~

Bootstraps the wallet-connect experience on the website's authorize page:
fetches the initial wallet and network data, creates and binds the components,
resumes an existing wallet session, and cleans up on unload.

``walletComponent.ts``
~~~~~~~~~~~~~~~~~~~~~~

One Algorand wallet's connection and the address-authorization flow. Each
supported wallet is rendered as its own card and driven by one instance, so a
failure in one wallet cannot take the others down with it. Defaults to the
``/api/v2/wallet`` API base, overridable per instance.

``evmWalletComponent.ts`` / ``evmConnectors.ts`` / ``evmBootstrap.ts``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The EVM half. The component mounts against ``/api/v2/wallet/login``;
``evmConnectors.ts`` holds the browser-only adapters that produce concrete
connectors (EIP-6963 injected wallets, and WalletConnect); ``evmBootstrap.ts``
wires them to the page.

``manageAdapters.ts`` / ``manageBridge.ts`` / ``manageBootstrap.ts``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Step-up authentication for the manage page. The adapter signs a message with
the wallet holding a given address on a given chain; the bridge runs the
privilege-expanding action; the bootstrap supplies CSRF and the API base.

``swapBootstrap.ts`` / ``swapBridge.ts``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Swap execution. The bridge is pure orchestration of a prepared swap --- sign
the group with the connected wallet, submit, wait for confirmation --- while
the bootstrap holds the opt-in handling, partial-group signing and the wallet
manager.

``notify.ts``
~~~~~~~~~~~~~

A framework-free notification seam, so no component has to know how the host
page shows a message.

``walletTestHarness.ts``
~~~~~~~~~~~~~~~~~~~~~~~~

A **test-only** mock wallet. It is shipped in ``src/`` rather than in a test
directory because the browser tests drive it as a wallet; it is not part of any
production path.

Development
-----------

.. code-block:: bash

   cd wallet
   npm install          # or npm ci, which is what CI uses
   npm run dev          # Vite dev server
   npm run build        # tsc && vite build
   npm run build:docs   # regenerate docs/api/frontend_api/ with TypeDoc

``npm run build:docs`` writes into ``docs/api/frontend_api/``, which is the
directory the toctree above points at --- so a renamed or added module needs
that command run, and its output committed, before the reference here resolves.

Testing
-------

.. code-block:: bash

   cd wallet
   npm run test          # jest, via jest.config.cjs
   npm run test:watch
   npm run test:coverage

**Coverage is enforced, not merely reported**: ``jest.config.cjs`` sets a 100%
threshold on statements, branches, functions and lines, so a new module arrives
covered or the suite fails.

Exactly two things are excluded, and both because they *cannot* be covered
rather than because covering them is awkward: ``*.d.ts``, which has no runtime
statements, and ``setupTests.ts``, which Jest loads before instrumentation.
Everything else in ``src/`` counts --- including the bootstraps and the test
harness. That is deliberate and recent: the config used to name five modules to
skip while four more carried ``/* istanbul ignore file */`` of their own, so a
reported "100%" covered seven files of twelve. The one that mattered was
``swapBootstrap.ts``, which publishes the whole ``window.asastatsSwap`` surface
--- anything added there landed outside the number by default.

Wallet integration
------------------

Algorand wallets through ``@txnlab/use-wallet``:

* **Pera Wallet** --- mobile and web
* **Defly Wallet** --- mobile
* **Lute Connect** --- browser extension
* other adapters the library supports

EVM wallets through the project's own connectors: EIP-6963 injected providers,
and WalletConnect via Reown. ``WALLET_CONNECT_PROJECT_ID`` in ``website/.env``
is what enables the second; with it empty, only browser extensions work.

Authentication flow
-------------------

1. the reader connects a wallet
2. the app fetches a nonce from the backend
3. the reader signs it with the wallet
4. the backend verifies the signature
5. the address is authorized, and the reader is redirected

Transaction types
-----------------

* **Payment transactions** --- for authentication
* **Application calls** --- smart contract interactions
* **Asset transfer** --- reward token claims, and swap legs
* **Atomic groups** --- swaps and other multi-transaction operations

File structure
--------------

.. code-block:: text

   wallet/src/
   ├── main.ts                    # entry point for the authorize page
   ├── walletComponent.ts         # one Algorand wallet, one card
   ├── evmWalletComponent.ts      # the EVM equivalent
   ├── evmConnectors.ts           # EIP-6963 and WalletConnect adapters
   ├── evmBootstrap.ts            # browser wiring for the EVM flow
   ├── manageAdapters.ts          # step-up signing
   ├── manageBridge.ts            # the privilege-expanding action
   ├── manageBootstrap.ts         # browser wiring for the manage page
   ├── swapBootstrap.ts           # opt-in, partial groups, wallet manager
   ├── swapBridge.ts              # sign, submit, confirm
   ├── notify.ts                  # notification seam
   ├── walletTestHarness.ts       # TEST-ONLY mock wallet
   ├── setupTests.ts              # jest setup
   ├── vite-env.d.ts              # Vite type definitions
   └── *.test.ts                  # one suite beside each module

Dependencies
------------

* **@txnlab/use-wallet** --- Algorand wallet management and transaction signing
* **algosdk** --- Algorand JavaScript SDK
* **vite** --- build tool and development server
* **jest** --- testing framework
* **typedoc** --- documentation generation
