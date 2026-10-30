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
file ``website/config/settings/production.py``:

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

  sudo tail -n 50 /var/www/asastats.com/logs/django-warning.log


Invalid HTTP_HOST header
^^^^^^^^^^^^^^^^^^^^^^^^

Django answers a request whose ``Host`` header is not in ``ALLOWED_HOSTS`` with
``DisallowedHost`` and logs "Invalid HTTP_HOST header". On the production host the usual
source is a scan by bare IP or an unknown name. nginx keeps those away from Django in two
places in ``deploy/roles/nginx/templates/``: the ``default_server`` block in
``nginx.ssl.conf`` refuses the TLS handshake for any other name, and the ``/api/v2/``
address location in ``site_server_block.conf`` returns ``444`` for hosts outside the
site's own names.

If you still see the message for a name you do use, add it to ``ALLOWED_HOSTS`` in
``config/settings/production.py`` and to the host pattern in ``site_server_block.conf``.


Static files
------------

A page 500s in production and nowhere else
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

  ValueError: Missing staticfiles manifest entry for 'foo/bar.js'

Production serves static files through ``ManifestStaticFilesStorage``, where
``{% static %}`` **raises** for a path with no entry in ``staticfiles.json``.
Development's storage returns the URL and lets the browser 404 it, so a
template naming a file that is not there is a 500 in production and a silent
nothing everywhere else, including in the test suite.

Two causes, in this order of likelihood:

* the deploy restarted gunicorn before running ``collectstatic``, so workers
  are serving new code against the old manifest. The role runs them in the
  right order for exactly this reason; a hand-run deploy has to as well.
* the template really does name a file nothing ships. ``{% static %}`` is not
  the place to find out: ``core/tests/test_static_manifest.py`` collects into a
  throwaway directory under the production storage and renders the pages, so
  this fails in the suite instead.

Note that a *missing* entry raises while a **stale** one does not: without
``--clear``, ``collectstatic`` leaves old hashed files in place on purpose, so
a reader holding a page from the previous release can still fetch its assets.

A router or widget cannot reach its own API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

  Refused to connect because it violates the document's Content Security Policy

The page cannot catch and explain this: the fetch never happens, so the
feature simply does nothing. The host is missing from ``connect-src`` in
``deploy/roles/nginx/templates/ssl.conf``.

Every widget already declares the hosts it calls, in its ``widget.toml``
``hosts`` list, and the CSP is a second copy of that list maintained by hand.
``widgethost/tests/test_csp_hosts.py`` sweeps the manifests against the
template so the two cannot drift again; a wildcard source counts, so a host
under ``https://*.nodely.dev`` needs no line of its own.

Remember the header ships with nginx, not with the code: until the snippet on
the host is updated and openresty reloaded, a correct repository does not fix
a live page.

Linux server errors
-------------------

Check killed processes:

.. code-block:: bash

  sudo dmesg -T | grep -Ei 'killed process'


To make the OOM killer much less likely to pick a service, add this to its
systemd unit (``-1000`` exempts it entirely):

.. code-block:: ini

  [Service]
  OOMScoreAdjust=-999

WebSocket and realtime
----------------------

Engine-backed widgets (e.g. historic) open a WebSocket to their own consumer, which
relays engine progress over a shared Channels-Redis bus. Common failure modes:

Consumer never reached
^^^^^^^^^^^^^^^^^^^^^^

The page renders but the consumer's ``connect`` never runs. If the browser's Network → WS
tab shows nothing, the socket was never created client-side. Confirm htmx loaded exactly
once (a second htmx core on the page silently drops ``ws-connect``) and that the
``ws-connect`` URL carries a real bundle. If instead the WS request shows a ``404``, the
route is not registered. Check the widget's ``routing.py`` is included and that
``runserver`` is serving ASGI/Daphne (``daphne`` listed above the staticfiles
app in ``INSTALLED_APPS``; this project registers that app as
``core.staticfiles.AsastatsStaticFilesConfig``, not by its Django name).


Handshake succeeds but the widget stays busy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A ``101 Switching Protocols`` means the consumer connected; if the widget then hangs, its
first engine call is failing or blocking; read the server log. A ``403`` from the engine
on the initial evaluate usually means the bundle has no stored address count yet
(processing writes it), while a connection error means the engine is not running or not
reachable.


Timeout reading from Redis
^^^^^^^^^^^^^^^^^^^^^^^^^^

``redis.exceptions.TimeoutError: Timeout reading from <host>`` in the consumer's receive
loop is the Channels bus, not the app cache. Check the two rules under *Realtime* in the
widgets docs (one Redis for both sides, a compatible set of pins): a newer ``redis-py``
(RESP3) against an older ``channels_redis`` produces exactly this timeout.


Debugging using headers
^^^^^^^^^^^^^^^^^^^^^^^

You can use a custom debugging middleware and inspect the headers
through your browser's DevTools/Network tab.

.. warning::

  This middleware copies the session cookie and a hash of ``SECRET_KEY`` into
  response headers. Use it on a development or testing host only, and remove it
  before the code reaches production.

.. code-block:: python
  :caption: website/config/settings/base.py

  MIDDLEWARE = [
      # ...
      "core.middleware.DebugEnvMiddleware",
  ]


.. code-block:: python
  :caption: website/core/middleware.py

  from django.conf import settings


  class DebugEnvMiddleware:
      """Stamp every response with which settings/session/cache the *serving*
      process actually loaded. Compare a normal page (WSGI) with a /widgets/…
      request (Daphne): any difference in SESSION or CACHE is the bug.
      """

      def __init__(self, get_response):
          self.get_response = get_response

      def __call__(self, request):
          response = self.get_response(request)
          cache_default = settings.CACHES.get("default", {})
          response["X-Debug-Env"] = (
              f"MODULE={getattr(settings, 'SETTINGS_MODULE', 'None')} | "
              f"SESSION={getattr(settings, 'SESSION_ENGINE', 'None')} | "
              f"CACHE_BACKEND={cache_default.get('BACKEND', 'None')} | "
              f"CACHE_LOC={cache_default.get('LOCATION', 'None')} | "
              f"CACHE_PFX={cache_default.get('KEY_PREFIX', 'None')} | "
              f"AUTH={request.user.is_authenticated}"
          )
          response["X-Debug-Cookie"] = request.META.get("HTTP_COOKIE", "MISSING")[:80]

          from django.core.cache import cache

          probe = f"probe:{request.META.get('HTTP_HOST','')}"
          cache.set(probe, "seen", 30)
          response["X-Debug-Cache-Probe"] = (
              f"{probe}={cache.get(probe)} | id={id(cache._cache) if hasattr(cache,'_cache') else 'na'}"
          )
          # also surface the raw session lookup:
          from importlib import import_module

          engine = import_module(settings.SESSION_ENGINE)
          sk = request.COOKIES.get("sessionid", "")
          s = engine.SessionStore(sk)
          response["X-Debug-Session"] = (
              f"key={sk[:6]} exists={s.exists(sk) if sk else 'no-key'} keys={list(s.keys())}"
          )

          import hashlib
          response["X-Debug-Secret"] = hashlib.sha256(settings.SECRET_KEY.encode()).hexdigest()[:12]

          return response
