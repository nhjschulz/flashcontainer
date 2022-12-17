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
from flashcontainer.byteconv import ByteConvert

from typing import Dict
from pathlib import Path


class CFileWriter(DM.Walker):

    def __init__(self, model: DM.Model, options: Dict[str, any]):
        super().__init__(model, options)

        cfilename = Path.joinpath(
            self.options.get("DESTDIR"),
            self.options.get("BASENAME") + ".c")

        hfilename = Path.joinpath(
            self.options.get("DESTDIR"),
            self.options.get("BASENAME") + ".h")
        self.cfile = cfilename.open(mode="w")
        self.hfile = hfilename.open(mode="w")

    def _write_both(self, s: str) -> None:
        """ Write same into h and c file"""

        self.hfile.write(s)
        self.cfile.write(s)

    def pre_run(self):
        print(
            f"Generating C-files "
            f'{Path.joinpath(self.options.get("DESTDIR"), self.options.get("BASENAME"))}.[ch].')

        banner = f"/* AUTOGENERATED by "\
            f"{self.options.get('PNAME')} {self.options.get('VERSION')} {self.options.get('DATETIME')}\n"\
            f" * cmd: {self.options.get('CMDLINE')}\n"\
            f" * Buildkey: {self.options.get('GUID')}\n"\
            f" * !! DO NOT EDIT MANUALLY !!\n"\
            f" */\n\n"
        self._write_both(banner)

        include_guard = f"PARGEN_HEADER_INCLUDED_{self.options.get('GUID').hex}"

        self.hfile.write(
            f"#ifndef {include_guard}\n#define {include_guard}\n\n"
            "#ifdef __cplusplus\n"
            "extern \"C\" {\n"
            "#endif\n\n"
            "#include <stdint.h>\n"
            "typedef struct sruct_pargen_header_type\n"
            "{\n"
            "    uint16_t id;\n"
            "    uint16_t major;\n"
            "    uint16_t minor;\n"
            "    uint16_t dataver;\n"
            "    uint32_t reserved;\n"
            "    uint32_t length;\n"
            "} pargen_header_type_t;\n\n"
            )

        self.cfile.write(f'#include "{self.options.get("BASENAME")+".h"}"\n\n')

    def post_run(self):
        self.hfile.write(
            "#ifdef __cplusplus\n"
            "}\n"
            "#endif\n#endif\n")

        self.cfile.close()
        self.hfile.close()

    _TYPE_MAPPING = {
        DM.ParamType.uint32: "uint32_t",
        DM.ParamType.uint8: "uint8_t",
        DM.ParamType.uint16: "uint16_t",
        DM.ParamType.uint64: "uint64_t",
        DM.ParamType.int8: "int8_t",
        DM.ParamType.int16: "int16_t",
        DM.ParamType.int32: "int32_t",
        DM.ParamType.int64: "int64_t",
        DM.ParamType.float32: "float",
        DM.ParamType.float64: "double",
        DM.ParamType.utf8: "char"
    }

    def begin_block(self, block: DM.Block) -> None:
        """Write block comment and header """

        self._write_both(
            f"/* BEGIN Block {self.ctx_block.name} in container "
            f"{self.ctx_container.name} @ {hex(self.ctx_block.addr)}\n")

        if block.comment is not None:
            self._write_both(" *\n")

            for line in block.comment.splitlines():
                self._write_both(" * " + line + "\n")
            self._write_both(" */\n")

        self.hfile.write("extern ")
        self._write_both(f"volatile const pargen_header_type_t {self.ctx_block.name}_blkhdr")

        self.cfile.write(
            " =\n{\n"
            f"    0x{block.header.id:04X},\n"
            f"    0x{block.header.version.major:04X},\n"
            f"    0x{block.header.version.minor:04X},\n"
            f"    0x{block.header.version.version:04X},\n"
            f"    0x00000000,\n"
            f"    0x{block.header.length:08X},\n"


            "}")

        self._write_both(";\n\n")

    def end_block(self, block: DM.Block) -> None:
        self._write_both(f"/* END Block {self.ctx_block.name}\n */\n\n")

    def begin_parameter(self, param: DM.Parameter) -> None:
        """Patch parameter bytes into intelhex object"""

        name = f"{self.ctx_block.name}_{param.name}"

        self._write_both(f"/* Parameter {name} @ {hex(param.offset)}\n")

        # write optional comment
        if param.comment is not None:
            for line in param.comment.splitlines():
                self._write_both(" * " + line + "\n")
        self._write_both(" */\n")

        self.hfile.write("extern ")
        self._write_both(
            f"volatile const "
            f"{CFileWriter._TYPE_MAPPING.get(param.type)} "
            f"{name}")

        element_size = ByteConvert.get_type_size(param.type)
        if (DM.ParamType.utf8 == param.type) or (element_size < len(param.value)):
            self._write_both(f"[{int(len(param.value)/ element_size)}]")

        self._format_value(param)

        self.cfile.write(" = ")
        self.cfile.write(ByteConvert.bytes_to_c_init(param.type, self.ctx_block.endianess, param.value))
        self._write_both(";\n\n")

    def _format_value(self, param: DM.Parameter) -> None:
        """Format raw data as C-initializer"""
