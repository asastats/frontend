# ASA Stats website's frontend

[![build](https://github.com/asastats/frontend/actions/workflows/build.yml/badge.svg)](https://github.com/asastats/frontend/actions/workflows/build.yml) [![docs](https://app.readthedocs.org/projects/asastats/badge/?version=latest)](https://asastats.readthedocs.io/en/latest/?badge=latest) [![codecov](https://codecov.io/gh/asastats/frontend/graph/badge.svg?token=DQC4SRY8J9)](https://codecov.io/gh/asastats/frontend) ![ansible-lint](https://github.com/asastats/frontend/actions/workflows/ansible-lint.yml/badge.svg) ![molecule](https://github.com/asastats/frontend/actions/workflows/molecule.yml/badge.svg) 


This repository contains the frontend and core web application code for ASA Stats, a platform that evaluates and presents ASA and NFT price information on the Algorand blockchain.

## Quick Start

For full installation, deployment, and troubleshooting instructions, please refer to the [Official Documentation](https://asastats.readthedocs.io/en/latest/).

### 1. Backend Setup (Django)
Requires Python 3 and PostgreSQL.

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements/development.txt

# Set environment variable and run
export DJANGO_SETTINGS_MODULE=website.settings.development
python manage.py migrate
python manage.py runserver
```

### 2. Frontend Setup (Vite / TypeScript)

Manages UI state, Web3 wallet connections, and interactive charts.

```bash
cd wallet
npm install
npm run build
```

## Testing

The project uses `pytest` for Python and `jest` for Typescript/Javascript.

```bash
# Backend tests
pytest --cov . --cov-report term-missing

# Frontend Typescript tests
cd wallet
npm run test:coverage

# Website Javascript tests
cd website
npm run test:coverage
```

## Project Architecture

The repository uses a component-based architecture split into modular Django apps and a Vite frontend:

* **`api`**: Frontend API (v2) for data processing and scoped endpoints.
* **`core`**: Main Django application (ORM, views, templates, permissions).
* **`nameservice`**: Integrations for NFDs and xChain accounts.
* **`walletauth`**: Web3 wallet authentication and cryptographic verifiers.
* **`widgethost`**: Registry and enforcement for modular interactive widgets.
* **`utils`**: Application-wide constants, charts, and caching utilities.
* **`frontend`**: Vite/TypeScript application utilizing `@txnlab/use-wallet` for transaction signing.

## Development Workflow

### Submodules

This repository relies on submodules. The `widgets` submodule is obligatory, and `permissiondapp` is optional.

To fetch their absolute latest remote updates:

```bash
git submodule update --remote website/widgets
git submodule update --remote website/permissiondapp
```

To revert changes and reset them to the specific commits this frontend repo expects:

```bash
git submodule update --init --recursive --force
```

### Linting

Python code formatting is enforced using `isort` and `black`. Be sure to exclude the submodules when running the formatter:

```bash
cd website/
isort .
black . --extend-exclude="widgets/" --extend-exclude="permissiondapp/"
```

## Deployment

Infrastructure provisioning and deployment are handled via **Ansible** targeting Ubuntu Server 24.04 LTS. Playbooks and environment configurations can be found in the `deploy/` directory.

```bash
# Example: Deploying project code to production
ansible-playbook --limit production --tags update-project-code deploy/site_playbook.yml
```
