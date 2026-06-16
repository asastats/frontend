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

