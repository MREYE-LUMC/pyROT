from __future__ import annotations

import logging
import os
from datetime import datetime
from subprocess import run

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pyROT"
year = datetime.now().year  # noqa: DTZ005
copyright_year = str(year) if year == 2025 else f"2025 - {year}"  # noqa: PLR2004
copyright = f"{copyright_year}, Jan-Willem Beenakker, Lennart Pors, Corné Haasjes"  # noqa: A001
author = "Jan-Willem Beenakker, Lennart Pors, Corné Haasjes"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["autoapi.extension", "myst_parser", "sphinx_design"]
myst_enable_extensions = ["colon_fence"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/MREYE-LUMC/pyROT",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/rayocular-toolbox",
            "icon": "fa-brands fa-python",
        },
        {
            "name": "MReye.nl",
            "url": "https://mreye.nl",
            "icon": "https://mreye.nl/icon.png",
            "type": "url",
        },
    ],
    "logo": {
        "text": "pyROT",
    },
    "show_toc_level": 1,
}

if os.getenv("READTHEDOCS") == "True":
    git_branch = os.getenv("READTHEDOCS_GIT_IDENTIFIER", "main")
else:
    try:
        git_branch = run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except:  # noqa: E722
        git_branch = "main"

logger.info("Building documentation for branch %s", git_branch)

html_context = {
    "edit_page_url_template": "{{ github_url }}/{{ github_user }}/{{ github_repo }}/tree/{{ github_version }}/{{ doc_path }}{{ file_name }}",
    "edit_page_provider_name": "GitHub",
    "github_user": "MREYE-LUMC",
    "github_repo": "pyROT",
    "github_version": git_branch,
    "doc_path": "docs",
}

# -- Options for autoapi ----------------------------------------------------
# https://sphinx-autoapi.readthedocs.io/en/latest/

autoapi_dirs = ["../pyrot"]
autoapi_root = "api"
autoapi_options = [
    "members",
    "show-inheritance",
    "show-module-summary",
]
