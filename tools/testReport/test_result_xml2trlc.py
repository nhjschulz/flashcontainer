"""Converts pytest results to corresponding TRLC output format.

    Author: Andreas Merkle (andreas.merkle@newtec.de)
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
import sys
import xml.etree.ElementTree as ET
from typing import IO, Optional

# Variables ********************************************************************

# Classes **********************************************************************

# Functions ********************************************************************

def _test_report_write_header(fd: IO) -> None:
    """Write test report header.

    Args:
        fd (IO): File descriptor
    """
    fd.write('package SwTests\n\n')
    fd.write('section "SW Test Results" {\n\n')

def _test_report_write_footer(fd: IO) -> None:
    """Write test report footer.

    Args:
        fd (IO): File descriptor
    """
    fd.write('}\n')

# pylint: disable=line-too-long
def _test_report_write_test_case_result(fd: IO, test_case_name: str, test_case_result: str, lobster_trace: Optional[str]) -> None:
    """Write test case result to test report.

    Args:
        fd (IO): File descriptor
        test_case_name (str): Name of the test case.
        test_case_result (str): Result of the test case (passed/failed).
        lobster_trace (Optional[str]): Test case id which is relates to the result.
    """
    test_case_id = test_case_name + "_result"
    fd.write(f'    SwTestCaseResult {test_case_id} {{\n')
    fd.write(f'        name = "{test_case_name}"\n')
    fd.write(f'        result = {test_case_result}\n')

    if lobster_trace is not None:
        fd.write(f'        relates = {lobster_trace}\n')

    fd.write('    }\n\n')

def _test_case_from_name(test_case_name: str) -> str:
    """Derive the TRLC test case id from a pytest test function name.

    Args:
        test_case_name (str): Name of the pytest test function, e.g. "test_swap".

    Returns:
        str: Qualified test case id, e.g. "SwTests.tc_swap".
    """
    name = test_case_name.split('[')[0]
    name = name.removeprefix('test_')

    return f"SwTests.tc_{name}"

def convert_test_report(xml_file: str, output_file: str) -> None:
    """Convert test report from XML format to corresponding TRLC format
        by considering the project specific defined TRLC model.

    Args:
        xml_file (str): The test report in XML format.
        output_file (str): The test report in TRLC format.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    with open(output_file, 'w', encoding='utf-8') as fd:
        _test_report_write_header(fd)

        for testcase in root.iter('testcase'):
            test_case_name = testcase.get('name')
            test_case_result = 'SwTestResult.PASSED'

            if testcase.find('failure') is not None:
                test_case_result = 'SwTestResult.FAILED'

            lobster_trace = None
            properties = testcase.find('properties')
            if properties is not None:
                for prop in properties.findall('property'):
                    if prop.get('name') == 'lobster-trace':
                        lobster_trace = prop.get('value')

            # The flashcontainer tests do not record a 'lobster-trace' property.
            # Derive the test case from the test function name instead:
            # test_<name> relates to SwTests.tc_<name>.
            if lobster_trace is None:
                lobster_trace = _test_case_from_name(test_case_name)

            _test_report_write_test_case_result(fd, test_case_name, test_case_result, lobster_trace)

        _test_report_write_footer(fd)

# Main *************************************************************************

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python parse_report.py <input_xml_file> <output_trlc_file>")
        sys.exit(1)

    test_report_xml_file = sys.argv[1]
    test_report_trlc_file = sys.argv[2]

    convert_test_report(test_report_xml_file, test_report_trlc_file)
