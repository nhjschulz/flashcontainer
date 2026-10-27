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

# ********** Argument validation **********
# Enable online report generation only if "online" argument is provided.
# If no argument is provided, only local file paths are used.
# If any other argument is provided, an error is raised.
LOBSTER_ONLINE_REPORT_ENABLE=0
if [ "$#" -gt 1 ]; then
    echo "Error: Too many arguments. Only optional 'online' is allowed." >&2
    exit 1
elif [ "$#" -eq 1 ]; then
    if [ "$1" == "online" ]; then
        LOBSTER_ONLINE_REPORT_ENABLE=1
    else
        echo "Error: Invalid argument '$1'. Only optional 'online' is allowed." >&2
        exit 1
    fi
fi


LOBSTER_TRLC=lobster-trlc
LOBSTER_REPORT=lobster-report
LOBSTER_RENDERER=lobster-html-report
LOBSTER_ONLINE_REPORT=lobster-online-report

OUTPUT_DIR=out

SW_REQ_LOBSTER_CONF=./lobster-trlc-sw-req.yaml
SW_REQ_LOBSTER_OUT=$OUTPUT_DIR/sw_req-lobster.json

SW_CONSTRAINT_LOBSTER_CONF=./lobster-trlc-sw-constraint.yaml
SW_CONSTRAINT_LOBSTER_OUT=$OUTPUT_DIR/sw_constraint-lobster.json

SW_ARCH_LOBSTER_CONF=./lobster-trlc-sw-arch.yaml
SW_ARCH_LOBSTER_OUT=$OUTPUT_DIR/sw_arch-lobster.json

SW_TEST_LOBSTER_CONF=./lobster-trlc-sw-test.yaml
SW_TEST_LOBSTER_OUT=$OUTPUT_DIR/sw_test-lobster.json

SW_TESTRESULT_LOBSTER_CONF=./lobster-trlc-sw-test-result.yaml
SW_TESTRESULT_LOBSTER_OUT=$OUTPUT_DIR/sw_test_result-lobster.json

SW_REQ_LOBSTER_REPORT_CONF=./lobster-report-sw-req.conf
SW_REQ_LOBSTER_REPORT_OUT=$OUTPUT_DIR/lobster-report-sw-req-lobster.json
SW_REQ_LOBSTER_ONLINE_REPORT_CONF=$OUTPUT_DIR/online_report_config.yaml

SW_REQ_LOBSTER_HTML_OUT=$OUTPUT_DIR/sw_req_tracing_online_report.html


# ********** Prepare output directory **********
if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
else
    rm -rf "$OUTPUT_DIR"/*
fi

# ********** SW-Requirements **********
$LOBSTER_TRLC --config "$SW_REQ_LOBSTER_CONF" --out "$SW_REQ_LOBSTER_OUT"

if [ $? -ne 0 ]; then
    exit 1
fi

$LOBSTER_TRLC --config "$SW_CONSTRAINT_LOBSTER_CONF" --out "$SW_CONSTRAINT_LOBSTER_OUT"

if [ $? -ne 0 ]; then
    exit 1
fi
# ********** SW-Arch **********
$LOBSTER_TRLC --config "$SW_ARCH_LOBSTER_CONF" --out "$SW_ARCH_LOBSTER_OUT"

if [ $? -ne 0 ]; then
    exit 1
fi

# ********** SW-Test **********
$LOBSTER_TRLC --config "$SW_TEST_LOBSTER_CONF" --out "$SW_TEST_LOBSTER_OUT"

if [ $? -ne 0 ]; then
    exit 1
fi

# ********** SW-Test Result **********
$LOBSTER_TRLC --config $SW_TESTRESULT_LOBSTER_CONF --out $SW_TESTRESULT_LOBSTER_OUT

if [ $? -ne 0 ]; then
    exit 1
fi

# ********** Combine all lobster intermediate files **********
$LOBSTER_REPORT --lobster-config "$SW_REQ_LOBSTER_REPORT_CONF" --out "$SW_REQ_LOBSTER_REPORT_OUT"

if [ $? -ne 0 ]; then
    exit 1
fi

# ********** LOBSTER Report conversion from local files to GIT URLS **********
if [ "$LOBSTER_ONLINE_REPORT_ENABLE" -eq "1" ]; then
    COMMIT_ID=$(git rev-parse HEAD)
    BASE_URL="https://github.com/nhjschulz/flashcontainer.git"
    echo "report: '$SW_REQ_LOBSTER_REPORT_OUT'" > "$SW_REQ_LOBSTER_ONLINE_REPORT_CONF"
    echo "commit_id: '$COMMIT_ID'" >> "$SW_REQ_LOBSTER_ONLINE_REPORT_CONF"
    echo "repo_root: './../..'" >> "$SW_REQ_LOBSTER_ONLINE_REPORT_CONF"
    echo "base_url: '$BASE_URL'" >> "$SW_REQ_LOBSTER_ONLINE_REPORT_CONF"
    cat $SW_REQ_LOBSTER_ONLINE_REPORT_CONF

    # lobster-online-report v1.0.1 fails to patch the input file without --out option.
    # Create temporary one with ".online" extension and replace it with the input afterwards.
    #
    $LOBSTER_ONLINE_REPORT --config "$SW_REQ_LOBSTER_ONLINE_REPORT_CONF" --out "$SW_REQ_LOBSTER_REPORT_OUT.online"
        if [ $? -ne 0 ]; then
        exit 1
    fi
    mv "$SW_REQ_LOBSTER_REPORT_OUT.online" "$SW_REQ_LOBSTER_REPORT_OUT"
fi

# ********** Create trace report **********
$LOBSTER_RENDERER --out "$SW_REQ_LOBSTER_HTML_OUT" "$SW_REQ_LOBSTER_REPORT_OUT"

if [ $? -ne 0 ]; then
    exit 1
fi
