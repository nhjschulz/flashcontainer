"""Provide packaging information metadata """

# BSD 3-Clause License
#
# Copyright (c) 2022-2023, Haju Schulz (haju.schulz@online.de)
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
#

import importlib.metadata as meta
import os
import sys
from typing import Tuple

import toml

__version__ = "???"
__author__ = "???"
__email__ = "???"
__repository__ = "???"
__license__ = "???"

def resource_path(relative_path: str) -> str:
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # pylint: disable=protected-access
        # pylint: disable=no-member
        base_path = sys._MEIPASS
    except Exception:  # pylint: disable=broad-except
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def init_from_metadata() -> Tuple[str, str, str, str, str]:
    """Initialize dunders from importlib.metadata

    Requires that the pacakge was installed.
    """

    my_metadata = meta.metadata('flashcontainer')
    return \
        my_metadata['Version'],\
        my_metadata['Author'],\
        my_metadata['Author-email'],\
        my_metadata['Project-URL'].replace("repository, ", ""),\
        my_metadata['License']



def init_from_toml() -> Tuple[str, str, str, str, str]:
    """Initialize dunders from pypackage.toml file

    Tried if package wasn't installed
    """

    toml_file = resource_path("pyproject.toml")
    data = toml.load(toml_file)

    return \
        data["project"]["version"],\
        data["project"]["authors"][0]["name"],\
        data["project"]["authors"][0]["email"],\
        data["project"]["urls"]["repository"],\
        data["project"]["license"]["text"]

try:
    __version__, __author__, __email__, __repository__, __license__ = init_from_metadata()

except meta.PackageNotFoundError:
    __version__, __author__, __email__, __repository__, __license__ = init_from_toml()
