Themes
======

The appearance picker offers three kinds of theme. Which ones appear is
``settings.AVAILABLE_THEMES``; the CSS for them is built from
``static/css/input.css``. Those two lists are separate by necessity --- Django
renders the picker, Tailwind builds the stylesheet, and neither can import from
the other --- so ``core.tests.test_context_processors`` asserts they agree. A theme
offered but not built renders as an unstyled page.

Ours
----

``asastats`` and ``asastats-dark``, defined inline in ``input.css``. Every value is
lifted from the swap modal's own token block, because the swap modal is the
design the rest of the site was moved onto.

Stock DaisyUI
-------------

Registered by name in the ``@plugin "./daisyui.mjs"`` block: ``nord``, ``dim``,
``abyss``, ``corporate``, ``retro``, ``cyberpunk``, ``valentine``, ``halloween``, ``garden``,
``aqua``, ``lofi``, ``luxury``, ``dracula``, ``autumn``, ``business``, ``lemonade``, ``silk``.

These ship with DaisyUI (MIT) and need no separate attribution.

Third-party --- attribution required
------------------------------------

The themes under ``static/css/themes/`` are **not ours**, and they come from two
sources under two licences.

Themes by **Dachi** --- `<https://github.com/dachinat>`_

* **Source**: `<https://github.com/dachinat/daisyui-themes>`_
* **Licence**: **CC BY 4.0** --- `<https://creativecommons.org/licenses/by/4.0/>`_

``andromeda``, ``ayudark``, ``everforest``, ``flexoki``, ``githubdark``, ``githublight``,
``gruvbox``, ``kanagawa``, ``monokai``, ``nightfox``, ``nightowl``, ``onedarkpro``,
``rosepine``, ``solarized``, ``tokyonight``, ``vscode``.

**Catppuccin** --- `<https://github.com/catppuccin/daisyui>`_

* **Licence**: **MIT**, Copyright (c) 2021 Catppuccin

``latte``, ``frappe``, ``macchiato``, ``mocha``. Shipped without the ``catppuccin-``
prefix the upstream package uses: the flavour names are distinctive on their
own, and the full names crowded the picker.

Only the CC BY set needs a credit in the interface. MIT is satisfied by keeping
the copyright notice at the top of each vendored file, which those four do, so
they are deliberately **absent** from ``settings.THEME_ATTRIBUTION`` --- that list
is the CC BY obligation, not a list of themes we did not write.

Dachi's ``catppuccin`` was removed when these four arrived: it was one dark
approximation of a palette that now ships in all four of its official
flavours.

CC BY 4.0 permits use, modification and redistribution **on condition that**
the author, the source and the licence are named, and that changes are
indicated. That is a licence term, not a courtesy, so the credit is carried in
three places --- deliberately, because each one covers a reader the others miss:

1. **The appearance picker** (``snippets/theme_picker.html``) --- a line naming the
   author and licence, with links. This is the copy an ordinary visitor can
   see, and it is rendered from ``settings.THEME_ATTRIBUTION`` so it cannot drift
   from the list of themes actually offered.
2. **The built stylesheet** --- ``build-tailwind.sh`` prepends a ``/*! ... */``
   banner to ``style.tw.css`` after the build. This is needed because the source
   files each carry the author's own banner, but Lightning CSS (which Tailwind
   uses to minify) strips even preserve-comments, so it does not survive on its
   own. Prepending it after the fact means the served CSS always carries it.
3. **This documentation** (``themes.rst``), for anyone reading the repository.

Changes made
^^^^^^^^^^^^

The vendored files are unmodified except for one line each: the upstream
``@plugin "daisyui/theme"`` is rewritten to ``@plugin "../daisyui-theme.mjs"``,
because this project uses the standalone Tailwind CLI and has no ``node_modules``
for ``daisyui/theme`` to resolve against. The author's banner is left intact.

Adding or removing a theme
--------------------------

Adding one of ours or a stock one:

1. register it in ``static/css/input.css`` (inline block, or the ``themes:`` list);
2. add its name to ``settings.AVAILABLE_THEMES``;
3. rebuild: ``./build-tailwind.sh``.

Removing a third-party theme means removing **all four** of:

1. ``static/css/themes/<name>.css``;
2. its ``@import`` in ``input.css``;
3. its entry in ``settings.AVAILABLE_THEMES``;
4. its entry in ``settings.THEME_ATTRIBUTION["themes"]``.

``test_core_context_processors_attributed_themes_are_offered`` fails if a
vendored file is left uncredited, or if a credited theme is no longer offered.
