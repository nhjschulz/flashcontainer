""" Checksum calculations
"""

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

import struct
from typing import NamedTuple

import crc

class CrcConfig(NamedTuple):
    """Configuration data for arbitrary CRCs

        poly(int): Generator polynomial to use in the CRC calculation.
                   The bits in this integer are the coefficients in the polynomial.
        bit_width(int): Number of bits for the CRC calculation. They have to match with
                        the generator polynomial
        init(int): Seed value for the CRC calculation
        revin(bool): Reflect each single input byte if True
        revout(bool): Reflect the final CRC value if True
        xor(bool): Xor the final result with the value 0xff before returning the solution
        access(int): Access size when swapping (1,2,4 or 8)
        swap(bool): Swap bytes with access size
    """
    poly: int = 0x04C11DB7
    width: int = 32
    init: int = 0xFFFFFFFF
    revin: bool = True
    revout: bool = True
    xor: bool = True
    access: int = 1
    swap: bool = False

    def __str__(self):
        return \
            f"polynomial:0x{self.poly:X}, {self.width} Bit, "\
            f"init:0x{self.init:X}, "\
            f"reverse in:{self.revin}, reverse out:{self.revout}, "\
            f"final xor:{self.xor}, " \
            f"access:{self.access}, swap:{self.swap}"


class Crc:
    """ Checksum processing
    """
    def __init__(self, cfg: CrcConfig):
        """Create Crc instance

        Args:
            cfg (CrcConfig): Configuration of the CRC algorithm
        """
        self.cfg = cfg
        self.calculator = crc.Calculator(
            crc.Configuration(
                polynomial=cfg.poly, width=cfg.width,
                init_value=cfg.init,
                reverse_input=cfg.revin, reverse_output=cfg.revout,
                final_xor_value=0 if cfg.xor is False else (0x1 << cfg.width)-1
            )
        )

    def __str__(self):
        return f"{self.cfg}"

    def checksum(self, data: bytearray) -> int:
        """Calculate CRC checksum over given bytes

            Args:
                bytes (bytearray): Input bytes

            Returns:
                checksum
        """

        return self.calculator.checksum(data)

    @staticmethod
    def _swap_access_16bit(data: bytearray) -> bytearray:

        result = bytearray()
        for i in range(0, len(data), 2):
            result.extend(struct.pack(">H", struct.unpack("<H", data[i:i + 2])[0]))

        return result

    @staticmethod
    def _swap_access_32bit(data: bytearray) -> bytearray:

        result = bytearray()
        for i in range(0, len(data), 4):
            result.extend(struct.pack(">I", struct.unpack("<I", data[i:i + 4])[0]))

        return result

    @staticmethod
    def _swap_access_64bit(data: bytearray) -> bytearray:

        result = bytearray()
        for i in range(0, len(data), 8):
            result.extend(struct.pack(">Q", struct.unpack("<Q", data[i:i + 8])[0]))

        return result

    def prepare(self, data: bytearray) -> bytearray:
        """Convert byte stream to match access method from configuration

        Args:
            bytes (bytearray): input byte array, must be multiple of access size long
            access (int): access width 1,2,4 or 8

        Returns:
            reordered bytearray
        """

        if self.cfg.swap is True:
            if self.cfg.access != 8:
                swapper = {
                    16: Crc._swap_access_16bit,
                    32: Crc._swap_access_32bit,
                    64: Crc._swap_access_64bit
                }
                return swapper[self.cfg.access](data)

        return data
