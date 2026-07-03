Troubleshooting
===============

Ansible output
--------------

Prior to playbook invocation:

.. code-block:: bash

  export ANSIBLE_STDOUT_CALLBACK=debug
  # export ANSIBLE_STDOUT_CALLBACK=yaml


Django errors
-------------

Django logging is configured in settings to use the SystemD logs. You can inspect
the logs by issuing the following command:

.. code-block:: bash

  sudo journalctl -u gunicorn-production_website.service

If you want logging to a file, replace the following variable in the settings
file `website/config/settings/production.py``:

.. code-block:: python

  LOGGING = {
      "version": 1,
      "disable_existing_loggers": False,
      "handlers": {
          "file": {
              "level": "WARNING",
              "class": "logging.FileHandler",
              "filename": BASE_DIR.parent.parent.parent / "logs" / "django-warning.log",
          },
      },
      "loggers": {
          "django": {
              "handlers": ["file"],
              "level": "WARNING",
              "propagate": True,
          },
      },
  }

You can then access the log with:

.. code-block:: bash

  sudo tail -n 50 /var/www/www.asastats.com/logs/django-warning.log


Invalid HTTP_HOST header
^^^^^^^^^^^^^^^^^^^^^^^^

https://stackoverflow.com/a/49817720/11703358

.. code-block:: bash

  if ( $host !~* ^(yourdomain.com|www.yourdomain.com)$ ) {
    return 444;
  }


Linux server errors
-------------------

Check killed processes:

.. code-block:: bash

  sudo dmesg -T | egrep -i 'killed process'+


The following setting will prevent OOM from killing the process:

.. code-block:: ini

  [Service]
  OOMScoreAdjust=-999

WebSocket and realtime
----------------------

Engine-backed widgets (e.g. historic) open a WebSocket to their own consumer, which
relays engine progress over a shared Channels-Redis bus. Common failure modes:

Consumer never reached
^^^^^^^^^^^^^^^^^^^^^^^

The page renders but the consumer's ``connect`` never runs. If the browser's Network → WS
tab shows nothing, the socket was never created client-side — confirm htmx loaded exactly
once (a second htmx core on the page silently drops ``ws-connect``) and that the
``ws-connect`` URL carries a real bundle. If instead the WS request shows a ``404``, the
route is not registered — check the widget's ``routing.py`` is included and that
``runserver`` is serving ASGI/Daphne (``daphne`` listed above
``django.contrib.staticfiles`` in ``INSTALLED_APPS``).


Handshake succeeds but the widget stays busy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A ``101 Switching Protocols`` means the consumer connected; if the widget then hangs, its
first engine call is failing or blocking — read the server log. A ``403`` from the engine
on the initial evaluate usually means the bundle has no stored address count yet
(processing writes it), while a connection error means the engine is not running or not
reachable.


Timeout reading from Redis
^^^^^^^^^^^^^^^^^^^^^^^^^^^

``redis.exceptions.TimeoutError: Timeout reading from <host>`` in the consumer's receive
loop is the Channels bus, not the app cache. Confirm the frontend and the engine target
the same Redis host, port and database, and that ``channels``, ``channels_redis`` and
``redis`` are pinned to a compatible set — a newer ``redis-py`` (RESP3) against an older
``channels_redis`` produces exactly this timeout.
