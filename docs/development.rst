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
  export DJANGO_SETTINGS_MODULE=asastats.settings.development


Activate Python environment:

.. code-block:: bash

  source frontend/bin/activate


Adding an alias can be useful:

.. code-block:: bash
  :caption: ~/.bashrc

  alias 'front'='cd /home/username/dev/frontend/asastats;source /home/username/dev/venvs/frontend/bin/activate'


Initial packages installation:

.. code-block:: bash

  (frontend) debian:~/dev/frontend/asastats$ pip install -r requirements/development.txt


Run development server
----------------------

.. code-block:: bash

  python manage.py runserver


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

  python -m pytest asastats/functional_tests/ -v


Javascript
^^^^^^^^^^

Install dependencies:

.. code-block:: bash

  npm install


Run tests:

.. code-block:: bash

  cd /home/username/dev/frontend/asastats
  npm run test  #  npm run test:coverage
