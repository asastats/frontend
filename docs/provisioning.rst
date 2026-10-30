Provisioning
============

Ansible is the Python package used to deploy the frontend infrastructure.

This guide is made for ``Ubuntu Server 24.04.4 LTS`` hosts, but it applies to many other Debian-based Linux distros.


Local machine requirements
--------------------------

Ansible installation
^^^^^^^^^^^^^^^^^^^^

If you don't use the project's Python environment, install the latest stable Ansible with ``pip``.
On Debian-based systems the Python 3 package is called ``python3-pip``.

.. code-block:: bash

  sudo apt-get install python3-pip

.. code-block:: bash

  pip3 install ansible --user


Server requirements/setup
-------------------------

Production
^^^^^^^^^^

SSH access
""""""""""

For most VPS providers, the **root** user is already configured and SSH access is allowed with the public key you provided.


Virtual machine
^^^^^^^^^^^^^^^

Local network setup
"""""""""""""""""""

Configuration for Ubuntu 24.04.4 server:

.. code-block:: bash
  :caption: /etc/netplan/50-cloud-init.yaml

  network:
    version: 2
    ethernets:
      enp0s3:
        dhcp4: false
        addresses:
          - 192.168.1.100/24
        routes:
          - to: default
            via: 192.168.1.1
        nameservers:
          addresses: [8.8.8.8, 8.8.4.4]


Activate it with ``sudo netplan apply``.


SSH access
""""""""""

The server needs ``openssh-server`` installed and running. Many GNU/Linux distros have Python 3 preinstalled.

.. code-block:: bash

  sudo apt-get install openssh-server python3


In a VM used for testing, create a temporary user. On first start it enables the root login with:

.. code-block:: bash

    tempuser@ubuntu:~# sudo passwd root


Ubuntu restricts SSH login for root, so allow it temporarily:

.. code-block:: bash

  sudo nano /etc/ssh/sshd_config
  PermitRootLogin yes


Copy your default identity's public key from the local machine with (use ``-i identity_file`` for a different identity):

.. code-block:: bash

    ssh-copy-id root@192.168.1.100


Delete the temporary user afterwards:

.. code-block:: bash

    ssh root@192.168.1.100 "userdel tempuser; rm -rf /home/tempuser"


Project provisioning
--------------------

.. warning::

  Before using in production, you need to update the content of the error pages in the ``website/templates/`` directory,
  as well as the ``static/auth_privacy.html`` and ``static/auth_terms.html`` HTML pages to reflect your company name.

From the ``deploy`` directory, provision your testing server with:

.. code-block:: bash

  # testing (virtual machine)
  ansible-playbook --limit=testing site_playbook.yml


Similarly, for your production server use:

.. code-block:: bash

  # production
  ansible-playbook --limit=production site_playbook.yml


To debug, add ``-vv`` or ``-vvvv`` for more verbose output:

.. code-block:: bash

  ansible-playbook -vv --limit=testing site_playbook.yml


Environment files
^^^^^^^^^^^^^^^^^

The playbook reads two ``.env`` files per environment and merges them, the
infrastructure one from ``deploy/`` and the application one from ``website/``:

.. code-block:: text

  deploy/.env.testing      website/.env.testing
  deploy/.env.production   website/.env.production

``deploy/.env-example`` and ``website/.env.example`` are the templates. Copy
rather than edit them: both are committed, and both are blank
where a secret belongs.

A key left blank does **not** override a key another file gave a value, so the
example files can be loaded alongside a real one without wiping it; a key blank
in every file is still written to the app's ``.env``, blank, because
``get_env_variable`` raises for an absent key where it returns ``""`` for an
empty one.

Upgrade system and project
^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this to upgrade the system and the Python packages to their latest versions:

.. code-block:: bash

  ansible-playbook --limit=production --tags=upgrade site_playbook.yml


Update project code
^^^^^^^^^^^^^^^^^^^

After the code changes, run this to apply them:

.. code-block:: bash

  ansible-playbook --limit=production --tags=update-project-code site_playbook.yml


Verifying the roles with Molecule
---------------------------------

The roles are exercised against a throwaway container rather than against a
server. This is what CI runs, and it is the fastest way to find out that a
role assumed something the host does not have:

.. code-block:: bash

  cd deploy
  pip install molecule ansible ansible-compat "molecule-plugins[docker]"
  molecule test --scenario-name ci

Four scenarios share one converge playbook: ``ci`` (the committed example env
files, which is what GitHub runs), ``default`` and ``production`` (your real
``.env.testing`` / ``.env.production``), and ``shared`` holding the playbooks
themselves.

Every scenario loads ``molecule/shared/.env.molecule`` first. That file exists
because ``manage.py`` refuses to run at all when a Django system check of level
ERROR fires (an empty ``SIMPLE_JWT_KEY`` is one), and the committed
example leaves that blank on purpose. Nothing in it is a secret and nothing in
it should reach a real host.

``molecule test`` also runs the sequence twice and fails if the second run
reports a change. Two things that make a task look changed when nothing was:
a script that rewrites identical files with new mtimes, and a ``changed_when``
that reads a message the command always prints.
