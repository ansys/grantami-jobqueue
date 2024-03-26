"""Sphinx documentation configuration file."""

import datetime
import os
from pathlib import Path
import re
import shutil

from ansys_sphinx_theme import (
    ansys_favicon,
    get_autoapi_templates_dir_relative_path,
    get_version_match,
    pyansys_logo_black,
)
import jupytext

from ansys.grantami.jobqueue import __version__

# Project information
project = "ansys-grantami-jobqueue"
now = datetime.datetime.now()
project_copyright = f"(c) {now.year} ANSYS, Inc. All rights reserved"
author = "ANSYS, Inc."
release = version = __version__

# Select desired logo, theme, and declare the html title
html_logo = pyansys_logo_black
html_theme = "ansys_sphinx_theme"
html_short_title = html_title = "PyGranta JobQueue"
html_favicon = ansys_favicon

cname = os.getenv("DOCUMENTATION_CNAME", "jobqueue.grantami.docs.pyansys.com")
"""The canonical name of the webpage hosting the documentation."""

# specify the location of your github repo
html_theme_options = {
    "github_url": "https://github.com/ansys/grantami-jobqueue",
    "show_prev_next": False,
    "show_breadcrumbs": True,
    "additional_breadcrumbs": [
        ("PyAnsys", "https://docs.pyansys.com/"),
        ("PyGranta", "https://grantami.docs.pyansys.com/"),
    ],
    "switcher": {
        "json_url": f"https://{cname}/versions.json",
        "version_match": get_version_match(__version__),
    },
    "check_switcher": False,
}

# Sphinx extensions
extensions = [
    "autoapi.extension",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_jinja",
    "nbsphinx",
    "enum_tools.autoenum",
    "sphinx_design",
    "sphinx.ext.napoleon",
]

napoleon_custom_sections = ["Parameters", "Notes", "Examples"]


# Configuration for Sphinx autoapi
autoapi_type = "python"
autoapi_dirs = ["../../src/ansys"]
autoapi_root = "api"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]
autoapi_template_dir = get_autoapi_templates_dir_relative_path(Path(__file__))
suppress_warnings = ["autosectionlabel.*", "autoapi.python_import_resolution", "autoapi."]
autoapi_python_use_implicit_namespaces = True
autoapi_keep_files = True
autoapi_render_in_single_page = ["class", "enum", "exception"]


def skip_submodules(app, what, name, obj, skip, options):
    if what == "module":
        skip = True
    return skip


def setup(sphinx):
    sphinx.connect("autoapi-skip-member", skip_submodules)


# sphinx
add_module_names = False

# sphinx.ext.autodoc
autodoc_typehints = "description"  # Remove typehints from signatures in docs
autodoc_typehints_description_target = "documented"
autodoc_member_order = "bysource"

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "openapi-common": ("https://openapi.docs.pyansys.com", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
    # kept here as an example
    # "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    # "numpy": ("https://numpy.org/devdocs", None),
    # "matplotlib": ("https://matplotlib.org/stable", None),
    # "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    # "pyvista": ("https://docs.pyvista.org/", None),
    # "grpc": ("https://grpc.github.io/grpc/python/", None),
}

# static path
html_static_path = ["_static"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# Generate section labels up to four levels deep
autosectionlabel_maxdepth = 4


# -- Examples configuration --------------------------------------------------
def _copy_examples_and_convert_to_notebooks(source_dir, output_dir, ignored_files_regex=None):
    """
    Recursively copies all files from the source directory to the output directory.

    Creates any necessary subfolders in the process. Python scripts with the ".py" extension
    are also converted to Jupyter notebooks with the ".ipynb" extension using Jupytext.

    Parameters
    ----------
    source_dir : Path
        The source directory to copy files from.
    output_dir : Path
        The output directory to copy files to and convert Python scripts.
    ignored_files_regex : str, optional
        A regular expression pattern to match ignored files. Files whose names match
        the pattern will be skipped. If None (default), no files are ignored.

    Raises
    ------
    RuntimeError
        If the output directory or any necessary subfolders cannot be created.

    Notes
    -----
    - This function uses pathlib.Path methods for working with file paths.
    - Any existing files in the output directory will be overwritten.
    - If a Python script cannot be converted to a Jupyter notebook, an exception is raised.

    Examples
    --------
    >>> _copy_examples_and_convert_to_notebooks("my_project/examples", "docs/notebooks", ignored_files_regex=r"^test.*")

    """
    if not source_dir.exists():
        raise ValueError(f"Source directory {source_dir.name} does not exist.")
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    ignored_files_re = re.compile(ignored_files_regex) if ignored_files_regex else None

    for file_source_path in source_dir.rglob("*"):
        if not file_source_path.is_file():
            continue

        matches_regex = ignored_files_re and ignored_files_re.match(file_source_path.name)
        is_rst_file = file_source_path.name.endswith(".rst")

        if matches_regex and not is_rst_file:
            print(f"Ignoring {file_source_path.name}")
            exclude_patterns.append(str(file_source_path.relative_to(source_dir)))
            continue

        rel_path = file_source_path.relative_to(source_dir)
        file_output_path = output_dir / rel_path

        file_output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Copying {file_source_path.name}")
        shutil.copy(file_source_path, file_output_path)

        if file_source_path.suffix == ".py":
            try:
                ntbk = jupytext.read(file_source_path)
                jupytext.write(ntbk, file_output_path.with_suffix(".ipynb"))
            except Exception as e:
                raise RuntimeError(f"Failed to convert {file_source_path} to notebook: {e}")


exclude_patterns = []

EXAMPLES_SOURCE_DIR = Path(__file__).parent.parent.parent.absolute() / "examples"
EXAMPLES_OUTPUT_DIR = Path(__file__).parent.absolute() / "examples"
BUILD_EXAMPLES = True if os.environ.get("BUILD_EXAMPLES", "false") == "true" else False
if BUILD_EXAMPLES:
    ipython_dir = Path("../../.ipython").absolute()
    os.environ["IPYTHONDIR"] = str(ipython_dir)

ignore_example_files = r"test.*" if BUILD_EXAMPLES else r"^(?!test)"

# Properly configure the table of contents for the examples/index.rst file
jinja_contexts = {
    "examples": {
        "build_examples": BUILD_EXAMPLES,
    }
}

_copy_examples_and_convert_to_notebooks(
    EXAMPLES_SOURCE_DIR,
    EXAMPLES_OUTPUT_DIR,
    ignore_example_files,
)

nbsphinx_prolog = """
Download this example as a :download:`Jupyter notebook </{{ env.docname }}.ipynb>` or a
:download:`Python script </{{ env.docname }}.py>`.

----
"""
