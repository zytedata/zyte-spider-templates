import sys
from pathlib import Path

project = "zyte-spider-templates"
copyright = "2023, Zyte Group Ltd"
author = "Zyte Group Ltd"
release = "0.7.0"

sys.path.insert(0, str(Path(__file__).parent.absolute()))  # _ext
extensions = [
    "_ext",
    "enum_tools.autoenum",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_reredirects",
    "sphinxcontrib.autodoc_pydantic",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"

intersphinx_mapping = {
    "python": (
        "https://docs.python.org/3",
        None,
    ),
    "scrapy": (
        "https://docs.scrapy.org/en/latest",
        None,
    ),
    "scrapy-poet": (
        "https://scrapy-poet.readthedocs.io/en/stable",
        None,
    ),
    "scrapy-zyte-api": (
        "https://scrapy-zyte-api.readthedocs.io/en/stable",
        None,
    ),
    "web-poet": (
        "https://web-poet.readthedocs.io/en/stable",
        None,
    ),
    "zyte-common-items": (
        "https://zyte-common-items.readthedocs.io/en/latest",
        None,
    ),
}

autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_model_show_json = False

# sphinx-reredirects
redirects = {
    "customization/page-objects": "pages.html",
}
