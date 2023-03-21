""" Intel hex data file writer"""

# BSD 3-Clause License
#
# Copyright (c) 2022-2023, Haju Schulz (haju.schulz@online.de)
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


from typing import Dict
from pathlib import Path

from intelhex import IntelHex

import flashcontainer.datamodel as DM
from flashcontainer.checksum import Crc, CrcConfig

class HexWriter(DM.Walker):
    """ Intel hex data file writer"""

    def __init__(self, model: DM.Model, options: Dict[str, any]):
        super().__init__(model, options)

        self.hexbytes = bytearray()
        self.ihex = IntelHex()
        self.filename = Path.joinpath(
            self.options.get("DESTDIR"),
            self.options.get("BASENAME") + ".hex")
        self.crc_filename = Path.joinpath(
            self.options.get("DESTDIR"),
            self.options.get("BASENAME") + ".crc")

    def pre_run(self) -> None:
        print(f"Generating intelhex file {self.filename}.")

    def begin_block(self, block: DM.Block) -> None:
        addr = block.addr
        if block.header is not None:
            data = block.get_header_bytes()
            self.hexbytes.extend(data)
            for byte in data:
                self.ihex[addr] = byte
                addr += 1

    def begin_gap(self, param: DM.Parameter):
        """Gaps are same as parameter as far as hex dumping is concerned."""

        self.begin_parameter(param)

    def begin_parameter(self, param: DM.Parameter):
        """Patch parameter bytes into intelhex object"""

        self.hexbytes.extend(param.value)
        addr = param.offset
        for byte in param.value:
            self.ihex[addr] = byte
            addr += 1

    def post_run(self):
        """ Save into intelhex file"""

        self.ihex.tofile(str(self.filename), format='hex')

        # create additional crc file with CRC32 checksum of hex data
        with open(self.crc_filename, "w", encoding="UTF-8") as crc_file:
            crc_file.write(f"0x{self._get_crc32():X}\n")

    def _get_crc32(self) -> int:
        """Calculate CRC32 over produced hex bytes"""

        crc_cfg = CrcConfig(
                width=32,
                poly=0x04C11DB7,
                init=0xFFFFFFFF,
                xor=0xFFFFFFFF,
                revin=True,
                revout=True,
                access=1,
                swap=False
            )

        crc_calculator = Crc(crc_cfg)

        return crc_calculator.checksum(self.hexbytes)
