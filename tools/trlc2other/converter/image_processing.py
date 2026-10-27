"""Image file procesing tools.

    Author: Norbert Schulz (norbert.schulz@newtec.de)
"""

# pyTRLCConverter - A tool to convert TRLC files to specific formats.
# Copyright (c) 2024 - 2025 NewTec GmbH
#
# This file is part of pyTRLCConverter program.
#
# The pyTRLCConverter program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# The pyTRLCConverter program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with pyTRLCConverter.
# If not, see <https://www.gnu.org/licenses/>.

# Imports **********************************************************************
import os
from pathlib import Path
from typing import List, Optional

from pyTRLCConverter.plantuml import PlantUML

# Variables ********************************************************************

# Classes **********************************************************************

# Functions ********************************************************************

def convert_plantuml_to_image(plantuml_file: str, dest_dir: str, directories: List[str]) -> Optional[Path]:
    """
    Convert PlantUML diagram to image file.
    """
    result = None

    file_path = locate_file(plantuml_file, directories)
    if file_path is not None:
        puml = PlantUML()
        puml.generate("png", file_path, dest_dir)

        file_dst_path = os.path.basename(file_path)
        file_dst_path = os.path.splitext(file_dst_path)[0]
        file_dst_path += ".png"

        # PlantUML uses as output filename the diagram name if available.
        # The diagram name may differ from the filename.
        # To aovid that a invalid reference
        # ensure that the generated filename is as expected.
        expected_dst_path = os.path.join(dest_dir, file_dst_path)
        if os.path.isfile(expected_dst_path) is False:
            raise FileNotFoundError(
                f"{file_path} diagram name ('@startuml <name>') may differ from file name,"
                f"expected {expected_dst_path}."
            )
        result = expected_dst_path

    return result


def locate_file(file_path: str, directories: List[str]) -> Optional[str]:
    """
    Locate a file by searching through the sources list if it 
    cannot be accessed by the given file_path.
    Args:
        file_path (str): The name of the file to locate.
        directories (List[str]): A list of directories to search
            for the file.
    Returns:
        str: The full path to the located file if found, otherwise None.
    """
    calculated_path = None

    # Is the path to the file invalid?
    if os.path.isfile(file_path) is False:
        # Maybe the path is relative to one of the source paths.
        for src_item in directories:
            if os.path.isdir(src_item):
                full_file_path = os.path.join(src_item, file_path)
                if os.path.isfile(full_file_path) is False:
                    full_file_path = None
                else:
                    calculated_path = full_file_path
                    break
    else:
        calculated_path = file_path

    return calculated_path

# Main *************************************************************************
