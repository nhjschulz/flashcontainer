"""Project specific reStructuredText converter functions.

    Author: Andreas Merkle (andreas.merkle@newtec.de)
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
from typing import Any
from pyTRLCConverter.base_converter import RecordsPolicy

# pylint: disable=wrong-import-order
from generic_rsl_rst_converter import GenericRslRstConverter

# Variables ********************************************************************

# Classes **********************************************************************


class TestCaseRstConverter(GenericRslRstConverter):
    """Custom Project specific reStructuredText converter for test cases.
    """
    def __init__(self, args: Any) -> None:
        """
        Initialize the custom reStructuredText converter.

        Args:
            args (Any): The parsed program arguments.
        """
        super().__init__(args)

        # Set project specific record handlers for the converter.
        self._set_project_record_handlers(
           {
                "Image": self._print_image,
                "Info": self._print_info,
                "PlantUML": self._print_plantuml,
           }
        )
        self._record_policy = RecordsPolicy.RECORD_CONVERT_ALL

    @staticmethod
    def get_description() -> str:
        """ Return converter description.

         Returns:
            str: Converter description
        """
        return "Convert test case definitions into project extended reStructuredText format."


# Functions ********************************************************************

# Main *************************************************************************
