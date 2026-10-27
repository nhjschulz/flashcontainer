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

rem Keep all environment variables local to this script.
setlocal

set TRLC_CONVERTER=pyTRLCConverter
set OUTPUT_DIR=out
set CONVERTER=converter/req2markdown.py
set TRANSLATION=converter/translation.json
set OUT_FORMAT=markdown

if not exist "%OUTPUT_DIR%" (
    md %OUTPUT_DIR%
) else (
    del /q /s "%OUTPUT_DIR%\*" >nul
)

%TRLC_CONVERTER%  --source=..\..\trlc\swe-req --include=..\..\trlc\model --verbose --out=%OUTPUT_DIR% --project=%CONVERTER% --translation=%TRANSLATION% %OUT_FORMAT% || goto :error

%TRLC_CONVERTER%  --source=..\..\trlc\swe-arch --include=..\..\trlc\model --include=..\..\trlc\swe-req --exclude=..\..\trlc\swe-req --verbose --out=%OUTPUT_DIR% --project=%CONVERTER% --translation=%TRANSLATION% %OUT_FORMAT% || goto :error

set CONVERTER=converter/tc2markdown.py

%TRLC_CONVERTER%  --source=..\..\trlc\swe-test --include=..\..\trlc\model --include=..\..\trlc\swe-req --exclude=..\..\trlc\swe-req --verbose --out=%OUTPUT_DIR% --project=%CONVERTER% --translation=%TRANSLATION% %OUT_FORMAT% || goto :error

goto finished

:error

:finished

endlocal
rem Restore the previous directory from the stack.
rem This allows the script to return to the original working directory.
popd