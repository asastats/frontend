Howto
=====

Build the stylesheet
--------------------

The site's CSS is built from ``website/static/css/input.css`` with the
**standalone Tailwind CLI** plus the **DaisyUI** plugin. There is no
``node_modules`` for it and no Sass: three files are fetched per machine, and
only the built ``style.tw.css`` is committed.

Fetch the toolchain once per machine --- the script picks the right binary for
your platform:

.. code-block:: bash

  cd website
  ./fetch-tailwind.sh

That writes three gitignored files into ``static/css/``: ``tailwindcss`` (the
standalone binary), ``daisyui.mjs`` and ``daisyui-theme.mjs``.

Then build:

.. code-block:: bash

  ./build-tailwind.sh          # one-shot, minified
  ./build-tailwind.sh --watch  # rebuild on change, Ctrl-C to stop

``build-tailwind.sh`` refuses to run with a missing toolchain rather than
producing a stylesheet without it, and it prepends the CC BY attribution banner
that Lightning CSS would otherwise strip --- see :doc:`themes` for what that
banner is for and for how to add or remove a theme.

**Commit ``static/css/style.tw.css`` with the change that caused it.** The
server does not build CSS; the built file is what ships. A template change that
introduces a utility class nobody has compiled yet renders unstyled in
production and nowhere else.

Minify the JavaScript
---------------------

Our own scripts are minified into ``static/build/js`` by:

.. code-block:: bash

  cd website
  ./build-static.sh

This one needs ``node`` and ``npm``, because it runs a pinned ``esbuild``
through ``npx``. Ansible installs both (``setuphost``), and the deploy runs the
script before ``collectstatic``.

Two things worth knowing about it:

* **The output is not committed.** ``static/build`` is gitignored, and in
  production it is placed *first* in ``STATICFILES_DIRS`` so ``collectstatic``
  prefers the minified copy of each file over the readable source of the same
  name. Templates always name the source --- ``{% static 'js/site.js' %}`` ---
  so nothing in a template changes between development, where the directory is
  absent, and production, where it is not.
* **It only replaces what actually changed.** Each file is built into a
  temporary directory and moved into place only when the bytes differ, then the
  script prints ``BUILD_UPDATED=<n>``. Rewriting an identical file would give it
  a new mtime, which makes ``collectstatic`` copy it again --- and that made
  both tasks report a change on every deploy.

Vendored bundles (``*.min*.js``, ``bundle.js``) are skipped: they are already
minified and are not ours to rebuild.

Build documentation
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


Caches, and which settings module uses what
-------------------------------------------

The cache backend is not one setting to switch on; each settings module already
answers the question for its own environment. Before changing one, check which
of these you are actually running:

``config.settings.development``
  ``DummyCache`` --- every write is discarded. Right for ``runserver``, where
  six views are ``cache_page``\ 'd and three of them for ninety minutes: a
  developer wants to see an edit now, not in an hour and a half. A Redis block
  sits commented out beneath it for when you need to reproduce a caching bug.

``config.settings.automated_tests``
  ``LocMemCache``, cleared before each test by the autouse fixture in the root
  ``conftest.py``. Deliberately not Redis: Django rolls the database back
  between tests but never clears the cache, so a Redis entry would outlive the
  run and make a failure depend on run history.

``config.settings.testing`` / ``config.settings.production``
  ``django_redis`` against ``REDIS_HOST``/``REDIS_PORT_LOCAL``/``REDIS_AUTH``
  from the environment, with ``KEY_PREFIX="website"``. Production also puts
  sessions in the cache (``SESSION_ENGINE`` = the cache backend) and messages in
  the session.

The ``redis`` role is provisioned unconditionally by ``deploy/site_playbook.yml``
--- it is in the role list, not something to uncomment --- and it configures a
**dedicated** instance on ``redis_port``, which ``deploy/group_vars/all/vars.yml``
takes from ``REDIS_PORT_LOCAL`` and defaults to 6380. The separate port is the
point: on a host that also runs the closed backend, 6379 is that backend's
replica and is read-only, and the app writes to its cache on every miss.
