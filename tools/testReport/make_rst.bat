@echo off
REM BSD 3-Clause License
REM
REM Copyright (c) 2025, NewTec GmbH
REM
REM Redistribution and use in source and binary forms, with or without
REM modification, are permitted provided that the following conditions are met:
REM
REM 1. Redistributions of source code must retain the above copyright notice, this
REM    list of conditions and the following disclaimer.
REM
REM 2. Redistributions in binary form must reproduce the above copyright notice,
REM    this list of conditions and the following disclaimer in the documentation
REM    and/or other materials provided with the distribution.
REM
REM 3. Neither the name of the copyright holder nor the names of its
REM    contributors may be used to endorse or promote products derived from
REM    this software without specific prior written permission.
REM
REM THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
REM AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
REM IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
REM DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
REM FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
REM DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
REM SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
REM CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
REM OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
REM OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

rem Store the current directory on the stack and change to the directory of this script.
rem This allows the script to be run from any directory.
rem The script will always use the directory where it is located as the working directory.
pushd %~dp0

pushd ..\plantUML
call get_plantuml.bat
popd

setlocal

set SRC_PATH=./src
set TESTS_PATH=./tests
set COVERAGE_REPORT=coverage
set REPORT_TOOL_PATH=%~dp0
set TEST_RESULT_REPORT_XML=sw_test_result_report.xml
set TEST_RESULT_REPORT_TRLC=sw_test_result_report.trlc
set TRLC_CONVERTER=pyTRLCConverter
set CONVERTER_DIR=../trlc2other/converter
set OUTPUT_DIR=out
set CONVERTER=%CONVERTER_DIR%/create_test_report_in_rst.py
set OUT_FORMAT=rst

if not exist "%OUTPUT_DIR%" (
    md %OUTPUT_DIR%
) else (
    del /q "%OUTPUT_DIR%\*" >nul
)

rem Create the sw test report and the coverage analysis.
pushd  ..\..
pytest %TESTS_PATH% -v --cov=%SRC_PATH% --cov-report=term-missing --cov-report=html:%REPORT_TOOL_PATH%/%OUTPUT_DIR%/%COVERAGE_REPORT% -o junit_family=xunit1 --junitxml=%REPORT_TOOL_PATH%/%OUTPUT_DIR%/%TEST_RESULT_REPORT_XML% || goto :error
popd

rem Convert sw test report XML to TRLC.
python test_result_xml2trlc.py ./%OUTPUT_DIR%/%TEST_RESULT_REPORT_XML% ./%OUTPUT_DIR%/%TEST_RESULT_REPORT_TRLC% || goto :error

rem Convert sw test report TRLC to reStructuredText.
%TRLC_CONVERTER% --source=..\..\trlc\swe-req --source=..\..\trlc\swe-test --source=..\..\trlc\model --exclude=..\..\trlc\swe-req --exclude=..\..\trlc\swe-test --source=%OUTPUT_DIR%\%TEST_RESULT_REPORT_TRLC% -o=%OUTPUT_DIR% --project=%CONVERTER% --verbose %OUT_FORMAT% || goto :error

goto finished

:error

:finished

endlocal
rem Restore the previous directory from the stack.
rem This allows the script to return to the original working directory.
popd