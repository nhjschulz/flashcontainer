"""Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# BSD 3-Clause License
#
# Copyright (c) 2025, NewTec GmbH
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Imports **********************************************************************
import os
import shutil
import fnmatch

from urllib.parse import urlparse
from sphinx.errors import ConfigError
from typing import Optional

# pylint: skip-file

# Variables ********************************************************************

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'flashcontainer'
copyright = '2022-2026, Haju Schulz'
author = 'Haju Schulz'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # https://www.sphinx-doc.org/en/master/usage/markdown.html
    'myst_parser',

    # https://github.com/sphinx-contrib/plantuml
    'sphinxcontrib.plantuml'
]

templates_path = ['_templates']
exclude_patterns = []

# Support restructured text and Markdown
source_suffix = ['.rst', '.md']

rst_prolog = """
.. include:: <s5defs.txt>

"""

# -- MyST parser configuration ---------------------------------------------------

# Configure MyST parser to generate GitHub-style anchors
myst_heading_anchors = 6

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'haiku'
html_static_path = ['_static']
html_style = 'custom.css'

html_last_updated_fmt = '%b %d, %Y'

# PlantUML is called OS depended and the java jar file is provided by environment variable.
plantuml_env = os.getenv('PLANTUML')
plantuml = []

# Classes **********************************************************************

# Functions ********************************************************************

# List of files to copy to the output directory.
#
# The source is relative to the sphinx directory.
# The destination is relative to the output directory.
files_to_copy = [
    {
        'source': '../testReport/out/coverage',
        'destination': 'coverage',
        'exclude': []
    },
    {
        'source': '../trlc2other/out',
        'destination': '.',
        'exclude': ['*.rst']
    }
]

def setup(app: any) -> None:
    """Setup sphinx.

    Args:
        app (any): The sphinx application.
    """
    app.connect('builder-inited', copy_files)

def copy_files(app: any) -> None:
    """Copy files to the output directory.

    Args:
        app (any): The sphinx application.
    """
    for files in files_to_copy:
        source = os.path.abspath(files['source'])
        destination = os.path.join(app.outdir, files['destination'])

        if not os.path.exists(destination):
            os.makedirs(destination)

        for filename in os.listdir(source):
            if not any(fnmatch.fnmatch(filename, pattern) for pattern in files['exclude']):
                full_file_name = os.path.join(source, filename)
                if os.path.isfile(full_file_name):
                    shutil.copy(full_file_name, destination)

def get_git_commit_hash_info() -> Optional[str]:
    """Get commit hash info string for current sandbox.

    Returns:
            str: Git commit hash info string.
            None: in case of missing git output or exception.
    """
    result = None

    try:
        import subprocess

        out,err = subprocess.Popen(
                ['git', 'show', '-s', '--format=%H'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE).communicate()
        if out:
            result = f" from commit {out.decode().strip()}"

    except Exception as e:
        pass

    return result

# Main *************************************************************************

if plantuml_env is None:
    raise ConfigError(
        "The environment variable PLANTUML is not defined to either the location "
        "of plantuml.jar or server URL.\n"
        "Set plantuml to either <path>/plantuml.jar or a server URL."
    )

if urlparse(plantuml_env).scheme in ['http', 'https']:
    plantuml = [plantuml_env]
else:
    if os.path.isfile(plantuml_env):
        plantuml = ['java', '-jar', plantuml_env]
    else:
        raise ConfigError(
            f"The environment variable PLANTUML points to a not existing file {plantuml_env}."
        )

html_last_updated_fmt += get_git_commit_hash_info()
