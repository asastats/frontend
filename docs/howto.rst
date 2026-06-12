Howto
=====

Build documenattion
-------------------

.. code-block:: bash

  cd docs
  make html


Requirements to build latexpdf documentation:

.. code-block:: bash

  sudo apt-get install texlive texlive-latex-extra latexmk


Then build the pdf with:

.. code-block:: bash

  make latexpdf


Setup Redis cache
-----------------

By default, the website uses database as the session engine and caches to memory.
If you want to switch to Redis, replace the existing `SESSION_ENGINE` setting and add `CACHES`:

.. code-block:: python

  # SESSION_ENGINE = "django.contrib.sessions.backends.db"
  SESSION_ENGINE = "django.contrib.sessions.backends.cache"
  CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
  }


There's an existing Ansible role for Redis and you can install it during provisioning
by uncommenting the related line in the `deploy/site_playbook.yml`.
