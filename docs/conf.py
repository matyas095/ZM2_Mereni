"""Konfigurace Sphinx dokumentace pro ZM2_Mereni."""

import os
import sys

sys.path.insert(0, os.path.abspath(".."))
project = "ZM2_Mereni"
author = "matyas095"
copyright = "2026, matyas095"
language = "cs"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "alabaster"
html_static_path = ["_static"]
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
