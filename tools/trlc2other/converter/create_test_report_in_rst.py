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
from typing import Optional, Any
from pyTRLCConverter.base_converter import RecordsPolicy
from pyTRLCConverter.ret import Ret
from pyTRLCConverter.rst_converter import RstConverter
from pyTRLCConverter.trlc_helper import Record_Object

# Variables ********************************************************************

# The name of the file containing the SW test cases.
# This is required for creating unique reStructuredText links.
TEST_CASES_FILE_NAME = "swe-test.rst"

# Classes **********************************************************************


class CustomRstConverter(RstConverter):
    """Custom Project specific reStructuredText converter responsible for converting the
        SW test case results into reStructuredText format.
    """

    def __init__(self, args: Any) -> None:
        """Initializes the converter.

        Args:
            args (Any): The parsed program arguments.
        """
        super().__init__(args)

        # Set project specific record handlers for the converter.
        self._set_project_record_handlers(
            {
                "SwTestCaseResult": self._append_test_case_result
            }
        )

        self._record_policy = RecordsPolicy.RECORD_SKIP_UNDEFINED

        self._test_case_results = []

    @staticmethod
    def get_description() -> str:
        """ Return converter description.

        Returns:
            str: Converter description
        """
        return "Convert SW test case results to reStructuredText format."

    def leave_file(self, file_name: str) -> Ret:
        """
        Leave a file.

        Args:
            file_name (str): File name

        Returns:
            Ret: Status
        """

        # Multiple document mode?
        if self._args.single_document is False:
            assert self._fd is not None
            self._print_test_case_results()

        return super().leave_file(file_name)

    # pylint: disable=unused-argument
    def _append_test_case_result(self, record: Record_Object, level: int, translation: Optional[dict]) -> Ret:
        """
        Append test case result.

        Args:
            record (Record_Object): Record object to convert.
            level (int): Current level of the record object.
            translation (Optional[dict]): Translation dictionary for the record object.
                                            If None, no translation is applied.

        Returns:
            Ret: Status
        """
        self._test_case_results.append(record)
        return Ret.OK

    def finish(self):
        """
        Finish the conversion process.
        """
        # Single document mode?
        if self._args.single_document is True:
            assert self._fd is not None
            self._print_test_case_results()

        return super().finish()

    def _get_table_row(self, test_case_result: Record_Object) -> list[str]:
        """Get the table row for the given test case.

        Args:
            test_case_result (Record_Object): Test case result.

        Returns:
            list[str]: Table row
        """
        test_case_result_attributes = test_case_result.to_python_dict()

        test_function_name = self._get_attribute(test_case_result, "name")
        test_result = self._get_attribute(test_case_result, "result")

        test_case = test_case_result_attributes["relates"]
        if test_case is None:
            test_case = self.rst_escape("N/A")
        elif isinstance(test_case, list) is True:
            test_case_links = []
            for tc in test_case:
                anchor_tag = tc.replace("SwTests.", TEST_CASES_FILE_NAME + "-").lower()
                test_case_links.append(self.rst_create_link(tc, anchor_tag))

            test_case = ", ".join(test_case_links)
        else:
            anchor_tag = test_case.replace("SwTests.", TEST_CASES_FILE_NAME + "-").lower()

            test_case = self.rst_create_link(test_case, anchor_tag)

        test_function_name = self.rst_escape(test_function_name)

        if test_result == "PASSED":
            test_result = self.rst_role(test_result, "green")
        elif test_result == "FAILED":
            test_result = self.rst_role(test_result, "red")

        row = [test_case, test_function_name, test_result]

        return row

    def _print_test_case_results(self) -> None:
        """Prints the software test case results.
        """
        column_titles = ["Test Case", "Test Function", "Test Result"]

        max_widths = [len(title) for title in column_titles]

        for test_case_result in self._test_case_results:
            row = self._get_table_row(test_case_result)
            max_widths = [max(max_widths[idx], len(row[idx])) for idx in range(len(row))]

        table_head = self.rst_create_table_head(column_titles, max_widths)
        self._fd.write(table_head)

        for record in self._test_case_results:
            self._print_test_case_result(record, max_widths)

    def _print_test_case_result(self, test_case_result: Record_Object, max_widths: list[int]) -> None:
        """Prints the software test case result.

        Args:
            test_case_result (Record_Object): Software test case result to print.
            max_widths (list[int]): Maximum widths of the columns.
        """
        row = self._get_table_row(test_case_result)

        markdown_table_row = self.rst_append_table_row(row, max_widths, False)
        self._fd.write(markdown_table_row)

# Functions ********************************************************************

# Main *************************************************************************
