#!/bin/bash

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

pushd ../plantUML
chmod +x get_plantuml.sh
. ./get_plantuml.sh
popd

SRC_PATH=./src
TESTS_PATH=./tests
COVERAGE_REPORT=coverage
REPORT_TOOL_PATH=./tools/testReport
TEST_RESULT_REPORT_XML=sw_test_result_report.xml
TEST_RESULT_REPORT_TRLC=sw_test_result_report.trlc
TRLC_CONVERTER=pyTRLCConverter
CONVERTER_DIR=../trlc2other/converter
OUTPUT_DIR=out
CONVERTER=$CONVERTER_DIR/create_test_report_in_rst.py
OUT_FORMAT=rst

if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
else
    rm -f "$OUTPUT_DIR"/*
fi

# Create the test report and the coverage analysis.
pushd ../..
pytest $TESTS_PATH -v --cov=$SRC_PATH --cov-report=term-missing --cov-report=html:$REPORT_TOOL_PATH/$OUTPUT_DIR/$COVERAGE_REPORT -o junit_family=xunit1 --junitxml=$REPORT_TOOL_PATH/$OUTPUT_DIR/$TEST_RESULT_REPORT_XML
popd

if [ $? -ne 0 ]; then
    exit 1
fi

# Convert XML test report to TRLC.
python test_result_xml2trlc.py ./$OUTPUT_DIR/$TEST_RESULT_REPORT_XML ./$OUTPUT_DIR/$TEST_RESULT_REPORT_TRLC

if [ $? -ne 0 ]; then
    exit 1
fi

# Convert TRLC test report to reStructuredText.
$TRLC_CONVERTER --source=../../trlc/swe-req --source=../../trlc/swe-test --source=../../trlc/model --exclude=../../trlc/swe-req --exclude=../../trlc/swe-test --source=$OUTPUT_DIR/$TEST_RESULT_REPORT_TRLC -o=$OUTPUT_DIR --project=$CONVERTER --verbose $OUT_FORMAT

if [ $? -ne 0 ]; then
    exit 1
fi
