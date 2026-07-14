# Deployment (Ansible)

Provisions a single host for the open-source portfolio tracker. The
tracker reaches the ASA Stats backend over HTTP and uses public Algorand
services, so a fork only needs its own server plus credentials.

## Layout

```
deploy/
  ansible.cfg              # inventory + tmp/host-key settings
  inventory.yml            # testing / production / ci hosts (edit ansible_host)
  collections/             # Galaxy collection requirements
  requirements.txt         # pip deps for lint + Molecule
  group_vars/              # all + per-environment (host_alias) vars
  site_playbook.yml        # 3 plays: load env -> bootstrap admin -> provision
  roles/                   # createuser setuphost redis postgresql
                           # projectsetup gunicorn nginx hardening
  molecule/                # shared scenario + ci/default/production importers
  .env-example             # infra-level variables (copy to .env.<env>)
```

## Two-tier environment files

Infrastructure variables live here in `deploy/.env.<environment>` (copy
`.env-example`). Application secrets live in the Django project's own
`website/.env.<environment>` and are merged in at runtime.

Required application keys (see `roles/projectsetup/tasks/environment.yml`):
`SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_NAME`, `DATABASE_USER`,
`DATABASE_PASSWORD`, `ASASTATS_API_URL`, `ASASTATS_API_KEY`,
`ASASTATS_API_TIMEOUT`, `ALGOD_URL`, `ALGOD_TOKEN`, `INDEXER_URL`,
`INDEXER_TOKEN`, `REDIS_URL`, `SIMPLE_JWT_KEY`, plus optional social-auth and
email keys. `website/.env-example` should ship placeholder values for every
required key so CI/Molecule can boot the app without a live backend.

The `redis` role provisions a **second** Redis instance, leaving any existing
`6379` server untouched. Its port comes from `REDIS_PORT_LOCAL` in the deploy
`.env` (default `6380`) and is rendered into the app's `.env` as
`REDIS_PORT_LOCAL`, so the instance and the app's cache always agree. The
app's `REDIS_AUTH` is derived from the same `REDIS_PASSWORD` used for the
instance's `requirepass`.

## Run

```bash
cd deploy
pip install ansible
ansible-galaxy collection install -r collections/requirements.yml
ansible-playbook site_playbook.yml --limit testing
```

`--limit testing|production` selects both the host group and the matching
`.env.<environment>` file.

## Test locally

```bash
cd deploy
pip install -r requirements.txt
ansible-lint
molecule test                       # default scenario (.env.testing)
molecule test --scenario-name ci    # uses .env-example placeholders
```

Requirements layering: the server installs
`website/requirements/production.txt`; Molecule and local-VM deploy tests use
the optional `testing.txt`; CI app tests use `development.txt`.
