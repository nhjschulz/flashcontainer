"""
Project specific Markdown converter for Generic.rsl types.

This module provides a project specific Markdown converter subclass with
support for the TRLC record types defined in Generic.rsl.

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
import os
import shutil
from typing import Optional
# pylint: disable=import-error
from pyTRLCConverter.ret import Ret
from pyTRLCConverter.markdown_converter import MarkdownConverter
from pyTRLCConverter.trlc_helper import Record_Object

# pylint: disable=wrong-import-order
from image_processing import convert_plantuml_to_image, locate_file

# Variables ********************************************************************

# Classes **********************************************************************


class GenericRslMarkdownConverter(MarkdownConverter):
    """Project specific Markdown converter subclass for generic.rsl types.
    """

    # pylint: disable-next=unused-argument
    def _print_info(self, info: Record_Object, level: int, translation: Optional[dict]) -> Ret:
        """Prints the information.

        Args:
            info (Record_Object): Information to print.
            level (int): Current level of the record object.
            translation (Optional[dict]): Translation dictionary for the record object.
                                            If None, no translation is applied.

        Returns:
           Ret: Status
        """
        assert self._fd is not None

        self._write_empty_line_on_demand()

        markdown_info = self._render(info.n_package.name,
                                     info.n_typ.name,
                                     "description",
                                     self._get_attribute(info, "description"))

        self._fd.write(markdown_info)
        self._fd.write("\n")

        return Ret.OK

    # pylint: disable-next=unused-argument
    def _print_plantuml(self, diagram: Record_Object, level: int, translation: Optional[dict]) -> Ret:
        """Prints a plantuml diagram.

        Args:
            diagram (Record_Object): Diagram to print.
            level (int): Current level of the record object.
            translation (Optional[dict]): Translation dictionary for the record object.
                                            If None, no translation is applied.

        Returns:
           Ret: Status
        """
        assert self._fd is not None

        image_file = convert_plantuml_to_image(
            self._get_attribute(diagram, "file_path"),
            self._args.out,
            self._args.source
        )

        if image_file is not None:
            self._write_empty_line_on_demand()
            markdown_image = self.markdown_create_diagram_link(
                os.path.basename(image_file),
                self._get_attribute(diagram, "caption")
            )
            self._fd.write(markdown_image)

        return Ret.OK

    # pylint: disable-next=unused-argument
    def _print_image(self, image: Record_Object, level: int, translation: Optional[dict]) -> Ret:
        """Prints the image.

        Args:
            image (Record_Object): Diagram to print.
            level (int): Current level of the record object.
            translation (Optional[dict]): Translation dictionary for the record object.
                                            If None, no translation is applied.

        Returns:
           Ret: Status
        """
        assert self._fd is not None

        image_file = locate_file(self._get_attribute(image, "file_path"), self._args.source)
        if image_file is not None:
            # Copy image image file to output folder.
            shutil.copy(image_file, self._args.out)

            self._write_empty_line_on_demand()

            markdown_image = self.markdown_create_diagram_link(
                os.path.basename(image_file),
                self._get_attribute(image, "caption")
            )
            self._fd.write(markdown_image)

        return Ret.OK

# Functions ********************************************************************

# Main *************************************************************************
