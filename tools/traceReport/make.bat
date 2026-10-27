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

REM ********** Argument validation **********
REM Enable online report generation only if "online" argument is provided.
REM If no argument is provided, only local file paths are used.
REM If any other argument is provided, an error is raised.

set LOBSTER_ONLINE_REPORT_ENABLE=0
if "%~1"=="" (
    REM No arguments provided, proceed normally.
) else if "%~1"=="online" (
    set LOBSTER_ONLINE_REPORT_ENABLE=1
) else (
    echo Error: Invalid argument "%~1". Only optional "online" is allowed. >&2
    exit /b 1
)

REM Keep all environment variables local to this script.
setlocal

pushd %~dp0

set LOBSTER_TRLC=lobster-trlc
set LOBSTER_REPORT=lobster-report
set LOBSTER_RENDERER=lobster-html-report
set LOBSTER_ONLINE_REPORT=lobster-online-report

set OUTPUT_DIR=out

set SW_REQ_LOBSTER_CONF=.\lobster-trlc-sw-req.yaml
set SW_REQ_LOBSTER_OUT=%OUTPUT_DIR%\sw_req-lobster.json

set SW_CONSTRAINT_LOBSTER_CONF=.\lobster-trlc-sw-constraint.yaml
set SW_CONSTRAINT_LOBSTER_OUT=%OUTPUT_DIR%\sw_constraint-lobster.json

set SW_ARCH_LOBSTER_CONF=.\lobster-trlc-sw-arch.yaml
set SW_ARCH_LOBSTER_OUT=%OUTPUT_DIR%\sw_arch-lobster.json

set SW_TEST_LOBSTER_CONF=.\lobster-trlc-sw-test.yaml
set SW_TEST_LOBSTER_OUT=%OUTPUT_DIR%\sw_test-lobster.json

set SW_TESTRESULT_LOBSTER_CONF=.\lobster-trlc-sw-test-result.yaml
set SW_TESTRESULT_LOBSTER_OUT=%OUTPUT_DIR%\sw_test_result-lobster.json

set SW_REQ_LOBSTER_REPORT_CONF=.\lobster-report-sw-req.conf
set SW_REQ_LOBSTER_REPORT_OUT=%OUTPUT_DIR%\lobster-report-sw-req-lobster.json
set SW_REQ_LOBSTER_ONLINE_REPORT_CONF=%OUTPUT_DIR%\online_report_config.yaml

set SW_REQ_LOBSTER_HTML_OUT=%OUTPUT_DIR%\sw_req_tracing_online_report.html

if not exist "%OUTPUT_DIR%" (
    md %OUTPUT_DIR%
) else (
    del /q /s "%OUTPUT_DIR%\*" >nul
)

REM ********** SW-Requirements **********
%LOBSTER_TRLC% --config %SW_REQ_LOBSTER_CONF% --out %SW_REQ_LOBSTER_OUT% || goto :error

%LOBSTER_TRLC% --config %SW_CONSTRAINT_LOBSTER_CONF% --out %SW_CONSTRAINT_LOBSTER_OUT% || goto :error

REM ********** SW-Arch **********
%LOBSTER_TRLC% --config %SW_ARCH_LOBSTER_CONF% --out %SW_ARCH_LOBSTER_OUT% || goto :error

REM ********** SW-Test **********
%LOBSTER_TRLC% --config %SW_TEST_LOBSTER_CONF% --out %SW_TEST_LOBSTER_OUT% || goto :error

REM ********** SW-Test Result **********
%LOBSTER_TRLC% --config %SW_TESTRESULT_LOBSTER_CONF% --out %SW_TESTRESULT_LOBSTER_OUT% || goto :error

REM ********** Combine all lobster intermediate files **********
%LOBSTER_REPORT% --lobster-config %SW_REQ_LOBSTER_REPORT_CONF% --out %SW_REQ_LOBSTER_REPORT_OUT% || goto :error

REM ********** LOBSTER Report conversion from local files to GIT URLS **********
if not %LOBSTER_ONLINE_REPORT_ENABLE% ==1 goto skip_online

    for /f "delims=" %%i in ('git rev-parse HEAD') do set COMMIT_ID=%%i
    set BASE_URL=https://github.com/nhjschulz/flashcontainer.git
    echo report: '%SW_REQ_LOBSTER_REPORT_OUT%' > %SW_REQ_LOBSTER_ONLINE_REPORT_CONF%
    echo commit_id: '%COMMIT_ID%' >> %SW_REQ_LOBSTER_ONLINE_REPORT_CONF%
    echo repo_root: '.\..\..' >> %SW_REQ_LOBSTER_ONLINE_REPORT_CONF%
    echo base_url: '%BASE_URL%' >> %SW_REQ_LOBSTER_ONLINE_REPORT_CONF%
    type "%SW_REQ_LOBSTER_ONLINE_REPORT_CONF%"

    REM lobster-online-report v1.0.1 fails to patch the input file without --out option.
    REM Create temporary one with ".online" extension and replace it with the input afterwards.
    REM
    %LOBSTER_ONLINE_REPORT% --config "%SW_REQ_LOBSTER_ONLINE_REPORT_CONF%" --out "%SW_REQ_LOBSTER_REPORT_OUT%.online"
    move /Y "%SW_REQ_LOBSTER_REPORT_OUT%.online" "%SW_REQ_LOBSTER_REPORT_OUT%" || goto :error

:skip_online

REM ********** Create trace report **********
%LOBSTER_RENDERER% --out %SW_REQ_LOBSTER_HTML_OUT% %SW_REQ_LOBSTER_REPORT_OUT% || goto :error

goto finished

:error

:finished

endlocal
popd
