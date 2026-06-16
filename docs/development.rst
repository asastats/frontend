Development
===========

Setup
-----

The requirements necessary to use this project on a development machine are:

.. code-block:: bash

  sudo apt-get install git python3 python3-venv postgresql postgresql-contrib


Python environment
^^^^^^^^^^^^^^^^^^

Create Python virtual environment:

.. code-block:: bash

  python3 -m venv frontend


Set an environment variable upon activation:

.. code-block:: bash
  :caption: /home/username/dev/venvs/frontend/bin/activate

  # at the end of the file
  export DJANGO_SETTINGS_MODULE=config.settings.development


Activate Python environment:

.. code-block:: bash

  source frontend/bin/activate


Adding an alias can be useful:

.. code-block:: bash
  :caption: ~/.bashrc

  alias 'front'='cd /home/username/dev/frontend/website;source /home/username/dev/venvs/frontend/bin/activate'


Initial packages installation:

.. code-block:: bash

  (frontend) debian:~/dev/frontend/website$ pip install -r requirements/development.txt


Linting
^^^^^^^

To maintain code quality and consistent formatting, use `isort` and `black`. 
First, navigate to the `website` directory:

.. code-block:: bash

  cd website/

Sort the Python imports alphabetically:

.. code-block:: bash

  isort .

Run `black` for code formatting, making sure to explicitly exclude the submodules:

.. code-block:: bash

  black . --extend-exclude="widgets/" --extend-exclude="permissiondapp/"


Submodules
^^^^^^^^^^

This project utilizes submodules for isolated feature sets. The `widgets` submodule is an obligatory requirement, while the `permissiondapp` submodule is an optional addition used by the ASA Stats website.

To fetch the absolute latest version of the obligatory `widgets` submodule:

.. code-block:: bash

  git submodule update --remote website/widgets

To fetch the absolute latest version of the optional `permissiondapp` submodule:

.. code-block:: bash

  git submodule update --remote website/permissiondapp

In case of changed code, or if you need to throw away local changes, you can revert the submodules to the exact versions the frontend repository expects:

.. code-block:: bash

  # reset to the version frontend has
  git submodule update --init --recursive --force


Run development server
----------------------

.. code-block:: bash

  python manage.py runserver


WalletConnect & xChain Requirements
-----------------------------------

To support mobile EVM wallets, set your public Reown project ID in your ``.env``.
If left empty, only browser extensions will work.

.. code-block:: bash

    # Create at https://dashboard.reown.com
    WALLET_CONNECT_PROJECT_ID=your_project_id_here

**xChain Note:** Account logins require the Algod ``/v2/teal/compile`` endpoint enabled on ``algod_instance()``.


PostgreSQL
----------

PostgreSQL setup in development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Database creation on development machine:

.. code-block:: bash

  root@debian:~# su - postgres
  postgres@debian:~# createdb frontend_db


Database user setup on development machine (CREATEDB is needed for running tests, while
pg_trgm extension is used for determining the similarity of text based on trigram matching):

.. code-block:: bash

  postgres@debian:~# psql
  postgres=# CREATE USER frontend_user WITH ENCRYPTED PASSWORD 'mypassword';
  postgres=# ALTER USER frontend_user CREATEDB;
  postgres=# ALTER DATABASE frontend_db OWNER TO frontend_user;
  postgres=# \connect frontend_db
  postgres=# CREATE EXTENSION IF NOT EXISTS pg_trgm;


Finally, under frontend web Python environemnt:

.. code-block:: bash

  python manage.py makemigrations
  python manage.py migrate


Tests
-----

Python
^^^^^^

Run all tests:

.. code-block:: bash

  cd /home/username/dev/frontend
  source /home/username/dev/venvs/frontend/bin/activate
  python -m pytest -v  # or just pytest -v, pytest -vvv for more verbose output


Run tests and show coverage report in terminal:

.. code-block:: bash

  pytest --cov=. --cov-report=term-missing


Run tests matching pattern:

.. code-block:: bash

  pytest -v -k test_profile_model_check_votes_and_permission_updates
  pytest -v -k "not integration_tests"


Run project's functional tests:

.. code-block:: bash

  python -m pytest website/functional_tests/ -v


Run widgets submodule unit tests:

The `widgets` submodule is an integral part of the project and depends heavily on the frontend repository. Therefore, testing widgets directly from within the frontend is an expected behavior for developers.

.. code-block:: bash

  PYTHONPATH=website pytest -v website/widgets -c website/widgets/pytest.ini


Typescript
^^^^^^^^^^

Install dependencies:

.. code-block:: bash

  cd /home/username/dev/frontend/frontend
  npm install
  npm run build


Run tests:

.. code-block:: bash

  cd /home/username/dev/frontend/website
  npm run test  #  npm run test:coverage


Javascript
^^^^^^^^^^

Install dependencies:

.. code-block:: bash

  npm install


Run tests:

.. code-block:: bash

  cd /home/username/dev/frontend/website
  npm run test  #  npm run test:coverage
