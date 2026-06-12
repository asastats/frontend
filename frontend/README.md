# Frontend package

The frontend is a TypeScript application built with Vite that provides the user interface for interacting
with the Algorand blockchain.

## Overview

The frontend is a TypeScript application that provides the user interface for interacting
with the Algorand blockchain. It uses the `@txnlab/use-wallet` library for wallet management
and integrates with a Django backend for authentication and data management.

## Architecture

The frontend follows a component-based architecture where each major functionality is
encapsulated in its own class. The main application orchestrates these components and
manages their lifecycle.

## Main components

* [App](api/frontend_api/main/classes/App.md)
* [WalletComponent](api/frontend_api/WalletComponent/classes/WalletComponent.md)

### App (main.ts)

Main application orchestrator that initializes and coordinates all components.

**Location**: `frontend/src/main.ts`

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

### WalletComponent

Handles individual wallet connections, authentication, and transaction signing.

**Location**: `frontend/src/WalletComponent.ts`

**Responsibilities**:

* Manage wallet connection/disconnection
* Handle user authentication with cryptographic signing
* Send test transactions
* Manage active account selection
* Render wallet state to UI

**Key methods**:

* `connect()` - Connects the wallet
* `disconnect()` - Disconnects the wallet
* `auth()` - Authenticates user with backend
* `sendTransaction()` - Sends test transaction

## Development

To work with the frontend:

```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start development server
npm run build        # Build for production
npm run test         # Run tests
npm run build:docs   # Generate TypeDoc documentation