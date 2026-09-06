Provisioning
============

``Ansible`` is Python package used to deploy frontend infrastructure.

This guide is made for ``Ubuntu Server 24.04.04 LTS`` hosts, but it's applicable for many other Debian based Linux/GNU distros.


Local machine requirements
--------------------------

Ansible installation
^^^^^^^^^^^^^^^^^^^^

If you don't use the project's Python environment, the most recent stable Ansible version is available through ``pip``
and its Python 3 version for Debian-based systems is called python3-pip.

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

For majority of VPS providers, **root** user is already configured and ssh access is allowed by provided public key.


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
          addresses: [8.8.8.8, 4.4.4.4]


Configuration from above is activated by `sudo netplan apply`.


SSH access
""""""""""

Server should have ``openssh-server`` installed and running. Many GNU/Linux have Python 3 preinstalled.

.. code-block:: bash

  sudo apt-get install openssh-server python3


For testing purposes in VM environment, a temporary user should be created. Upon first start it will enable the root login by running:

.. code-block:: bash

    tempuser@ubuntu:~# sudo passwd root


In Ubuntu ssh login for root is restricted, so it should be temporary allowed:

.. code-block:: bash

  sudo nano /etc/ssh/sshd_config
  PermitRootLogin yes


Default identity public key copying (use -i identity_file for different identity) from the local machine is issued by:

.. code-block:: bash

    ssh-copy-id root@192.168.1.100


Temporary user should be deleted afterwards:

.. code-block:: bash

    ssh root@192.168.1.100 "userdel tempuser; rm -rf /home/tempuser"


Project provisioning
--------------------

.. warning::

  Before using in production, you need to update the content of the error pages in the ``website/templates/`` directory,
  as well as the ``static/auth_privacy.html`` and ``static/auth_terms.html`` HTML pages to reflect your company name.

Use the following commands from the `deploy` directory to provision the website on your testing server:

.. code-block:: bash

  # testing (virtual machine)
  ansible-playbook --limit=testing site_playbook.yml


Similarly, for your production server use:

.. code-block:: bash

  # production
  ansible-playbook --limit=production site_playbook.yml


For debugging purpose, add `-vv` or `-vvvv` for more verbose output:

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
rather than edit them --- both are committed, and both are deliberately blank
where a secret belongs.

A key left blank does **not** override a key another file gave a value, so the
example files can be loaded alongside a real one without wiping it; a key blank
in every file is still written to the app's ``.env``, blank, because
``get_env_variable`` raises for an absent key where it returns ``""`` for an
empty one.

Upgrade system and project
^^^^^^^^^^^^^^^^^^^^^^^^^^

Issue the following command if you want to fully upgrade system and Python packages to the latest versions:

.. code-block:: bash

  ansible-playbook --limit=production --tags=upgrade site_playbook.yml


Update project code
^^^^^^^^^^^^^^^^^^^

After code has changed, issue the following command to apply those changes:

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
ERROR fires --- an empty ``SIMPLE_JWT_KEY`` is one --- and the committed
example leaves that blank on purpose. Nothing in it is a secret and nothing in
it should reach a real host.

``molecule test`` also runs the sequence twice and fails if the second run
reports a change. Two things that make a task look changed when nothing was:
a script that rewrites identical files with new mtimes, and a ``changed_when``
that reads a message the command always prints.
