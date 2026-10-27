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
#

# ********** Argument validation **********
# Enable online report generation only if "online" argument is provided.
# If no argument is provided, only local file paths are used.
# If any other argument is provided, an error is raised.
ONLINE_REPORT_OPTION=''
if [ "$#" -gt 1 ]; then
    echo "Error: Too many arguments. Only optional 'online' is allowed." >&2
    exit 1
elif [ "$#" -eq 1 ]; then
    if [ "$1" == "online" ]; then
        ONLINE_REPORT_OPTION="online"
    else
        echo "Error: Invalid argument '$1'. Only optional 'online' is allowed." >&2
        exit 1
    fi
fi

# Create reStructured Text documentation from TRLC models and files.
(cd trlc2other; ./make_rst.sh)

# Create unit test reports
(cd testReport; ./make_rst.sh)

# Create tracing report from TRLC and source files.
(cd traceReport; ./make.sh $ONLINE_REPORT_OPTION)

#Create HTML documentation.
(cd plantUML; . ./get_plantuml.sh; cd ..;cd deployDoc; make html)
