Frontend package
================

The frontend is a TypeScript application built with Vite that provides the user interface for interacting
with the Algorand blockchain.

Overview
--------

The frontend is a TypeScript application that provides the user interface for interacting
with the Algorand blockchain. It uses the `@txnlab/use-wallet` library for wallet management
and integrates with a Django backend for authentication and data management.

Architecture
------------

The frontend follows a component-based architecture where each major functionality is
encapsulated in its own class. The main application orchestrates these components and
manages their lifecycle.

Main components
---------------

.. toctree::
   :maxdepth: 2

   api/frontend_api/main/classes/App.md
   api/frontend_api/walletComponent/classes/WalletComponent.md

App (main.ts)
~~~~~~~~~~~~~

Main application orchestrator that initializes and coordinates all components.

**Location**: ``frontend/src/main.ts``

**Responsibilities**:

* Initialize application on DOM content loaded
* Fetch initial wallet and network data
* Create and bind all UI components
* Manage application lifecycle and cleanup
* Handle wallet session resumption

**Key features**:

* Component lifecycle management
* Error handling for initialization
* Proper cleanup on page unload
* Coordination between components

WalletComponent
~~~~~~~~~~~~~~~

Handles individual wallet connections, authentication, and transaction signing.

**Location**: ``frontend/src/WalletComponent.ts``

**Responsibilities**:

* Manage wallet connection/disconnection
* Handle user authentication with cryptographic signing
* Send test transactions
* Manage active account selection
* Render wallet state to UI

**Key methods**:

* ``connect()`` - Connects the wallet
* ``disconnect()`` - Disconnects the wallet
* ``auth()`` - Authenticates user with backend
* ``sendTransaction()`` - Sends test transaction

Development
-----------

To work with the frontend:

.. code-block:: bash

   cd frontend
   npm install          # Install dependencies
   npm run dev          # Start development server
   npm run build        # Build for production
   npm run test         # Run tests
   npm run build:docs   # Generate TypeDoc documentation

Testing
-------

The frontend includes comprehensive testing with Jest:

.. code-block:: bash

   npm run test         # Run tests once
   npm run test:watch   # Run tests in watch mode
   npm run test:coverage # Run tests with coverage

Wallet integration
------------------

The application supports multiple Algorand wallets through `@txnlab/use-wallet`:

* **Pera Wallet** - Mobile and Web
* **Defly Wallet** - Mobile
* **Lute Connect** - Browser extension
* **Other compatible wallets**

Authentication flow
-------------------

1. User connects wallet
2. Application fetches nonce from backend
3. User signs nonce with wallet
4. Backend verifies signature
5. User is authenticated and redirected

Transaction types
-----------------

* **Payment transactions** - For authentication
* **Application calls** - Smart Contract interactions
* **Asset transfer** - For reward token claims
* **Atomic groups** - Complex multi-transaction operations

File structure
--------------

.. code-block:: text

   frontend/src/
   ├── WalletComponent.ts            # Individual wallet management
   ├── WalletComponent.test.ts       # Tests for wallet component
   ├── main.ts                       # Main application orchestrator
   ├── main.test.ts                  # Tests for main application
   ├── setupTests.ts                 # Test setup configuration
   └── vite-env.d.ts                 # Vite type definitions

Dependencies
------------

* **@txnlab/use-wallet** - Wallet management and transaction signing
* **algosdk** - Algorand JavaScript SDK
* **vite** - Build tool and development server
* **jest** - Testing framework
* **typedoc** - Documentation generation
