# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import os
import re
import subprocess
import sys

import django

sys.path.insert(0, os.path.abspath("../website"))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Set Django settings
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.development"

# **Placeholders for every setting the documented modules require outright.**
#
# `get_env_variable` raises `ImproperlyConfigured` when a name has no default,
# which is right for a server - a deployment missing its database or its mail
# credentials should refuse to start - and fatal for autodoc, which only wants
# to import the module and read its docstrings.
#
# **What made this worth chasing: the local build and the Read the Docs build
# fail differently.** A developer has `website/.env`, so locally only
# `EMAIL_HOST_USER` was missing and the damage looked like one warning on
# `config.settings.production`. There is no `.env` on Read the Docs, and the
# same build produced thirteen - `api.views`, `core.views`, `walletauth.views`
# and every `urls` module among them. None of that was visible from here.
#
# Two distinct causes behind those thirteen: the three `DATABASE_*` names, and
# an empty `SECRET_KEY`. The latter has a default of `""` in `base.py`, so it
# never raises on read - Django raises later, when something actually signs
# with it, which is why the failures landed on views and URL configurations
# rather than on settings.
#
# Every one of these is read at import to build a dictionary. Nothing here opens
# a file, connects to a database or sends mail, so a placeholder documents the
# module exactly as a real value would.
#
# `setdefault`, so a real environment always wins. The values are deliberately
# unusable: a path that does not exist, an address in a reserved TLD, and a
# key that says what it is.
os.environ.setdefault("PGPASSFILE", "/nonexistent/docs-build.pgpass")
os.environ.setdefault("EMAIL_HOST_USER", "docs-build@example.invalid")
os.environ.setdefault("EMAIL_HOST_PASSWORD", "unused-by-the-docs-build")
os.environ.setdefault("DATABASE_NAME", "docs_build")
os.environ.setdefault("DATABASE_USER", "docs_build")
os.environ.setdefault("DATABASE_PASSWORD", "unused-by-the-docs-build")
os.environ.setdefault("SECRET_KEY", "docs-build-placeholder-not-a-real-secret")


django.setup()


# -- Project information -----------------------------------------------------

project = "ASA Stats frontend"
copyright = "2026, ASA Stats DAO"
authors = "Ivica Paleka"

# The full version, including alpha/beta/rc tags
from config import __version__

release = __version__

# -- General configuration ---------------------------------------------------

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = [".rst", ".md"]

master_doc = "index"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "myst_parser",
]

# Generate TypeDoc documentation if not on ReadTheDocs
if not os.environ.get("READTHEDOCS"):
    frontend_path = os.path.abspath("../frontend/frontend")
    if os.path.exists(frontend_path):
        print("Generating TypeDoc documentation...")
        try:
            subprocess.run(
                ["npm", "run", "build:docs"],
                cwd=frontend_path,
                check=True,
            )
            # Delete generated README.md and modules.md files
            import glob

            for file_path in glob.glob(
                os.path.join(
                    project_root, "docs", "api", "frontend_api", "**", "README.md"
                ),
                recursive=True,
            ):
                os.remove(file_path)
            for file_path in glob.glob(
                os.path.join(
                    project_root, "docs", "api", "frontend_api", "**", "modules.md"
                ),
                recursive=True,
            ):
                os.remove(file_path)
            # Remove cross-references to README.md from other generated .md files
            for root, dirs, files in os.walk(
                os.path.join(project_root, "docs", "api", "frontend_api")
            ):

                for file in files:
                    if file.endswith(".md") and file not in ("README.md", "modules.md"):
                        filepath = os.path.join(root, file)
                        with open(filepath, "r") as f:
                            lines = f.readlines()

                        with open(filepath, "w") as f:
                            for line in lines:
                                # Safely convert [Link Text](../../README.md)->Link Text
                                # without deleting the entire surrounding line.
                                safe_line = re.sub(
                                    r"\[([^\]]+)\]\((?:\.\./)+README\.md\)", r"\1", line
                                )
                                f.write(safe_line)

                        # Remove leading horizontal rules or other transitions
                        with open(filepath, "r") as f:
                            lines = f.readlines()

                        # Define a list of common reStructuredText transition markers
                        transition_markers = [
                            "---",
                            "===",
                            "***",
                            "___",
                            "+++",
                            "~~~",
                            "^^^",
                            "```",
                        ]

                        # Filter out leading transition lines
                        filtered_lines = []
                        transition_found = False
                        for line in lines:
                            if (
                                not transition_found
                                and line.strip() in transition_markers
                            ):
                                transition_found = True
                                continue
                            filtered_lines.append(line)

                        with open(filepath, "w") as f:
                            f.writelines(filtered_lines)
        except subprocess.CalledProcessError:
            print("TypeDoc generation failed - continuing without frontend docs")

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "api/frontend_api/**/README.md",
    "api/frontend_api/**/modules.md",
]

# Suppress strict validation warnings caused by auto-generated Typedoc Markdown
suppress_warnings = [
    "myst.xref_missing",
    "toc.not_included",
]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
# html_theme = 'furo'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


html_logo = "_static/logo.png"
html_favicon = "_static/favicon.ico"

latex_documents = [
    (
        "index",
        "asastats-frontend.tex",
        "ASA Stats frontend documentation",
        authors,
        "howto",
    )
]
