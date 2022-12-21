# BSD 3-Clause License
#
# Copyright (c) 2022, Haju Schulz (haju.schulz@online.de)
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

import flashcontainer.datamodel as DM

from typing import Dict
from pathlib import Path


class GnuLdWriter(DM.Walker):

    def __init__(self, model: DM.Model, options: Dict[str, any]):
        super().__init__(model, options)
        self.ldfile = None

    def pre_run(self) -> None:
        filename = Path.joinpath(
            self.options.get("DESTDIR"),
            self.options.get("BASENAME") + ".ld")

        print(f"Generating GNU Linker script {filename}.")

        self.ldfile = filename.open(mode='w')

        self.ldfile.write(
            f"/* AUTOGENERATED by {self.options.get('PNAME')} "
            f"{self.options.get('VERSION')} {self.options.get('DATETIME')}\n"
            f" * GNU Linker script definitions - include to main script using 'INCLUDE {self.options.get('FN')}'\n"
            f" * cmd: {self.options.get('CMDLINE')}\n"
            f" * Buildkey: {self.options.get('GUID')}\n"
            f" * !! DO NOT EDIT MANUALLY !!\n"
            " */\n\n"
        )

    def begin_container(self, container: DM.Container) -> None:
        self.ldfile.write(f"/* Begin flash container {container} */")

    def end_container(self, container: DM.Container) -> None:
        self.ldfile.write(f"/* End flash container {container} */\n")

    def begin_block(self, block: DM.Block) -> None:
        self.ldfile.write("\n")
        if block.header is not None:
            header_param = f"{block.name}_blkhdr"
            self.ldfile.write(f"{header_param: <40} = {hex(block.addr)};\n")

    def begin_parameter(self, param: DM.Parameter) -> None:
        """Add parameter name and address mapping"""

        name = f"{self.ctx_block.name}_{param.name}"

        # write multiline comment before definition
        comment_lines = None
        if param.comment is not None:
            comment_lines = param.comment.splitlines()
            if (len(comment_lines) > 1):
                self.ldfile.write("/* ")
                for line in comment_lines:
                    self.ldfile.write(" * " + line + "\n")
                self.ldfile.write("*/\n")

                comment_lines = None

        self.ldfile.write(f"{name: <40} = {hex(param.offset)};")
        if comment_lines is not None:
            self.ldfile.write(f" /* {comment_lines[0]} */")

        self.ldfile.write("\n")

    def post_run(self):
        """Close output file"""

        self.ldfile.close()
