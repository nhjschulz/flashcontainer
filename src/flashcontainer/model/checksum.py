""" Checksum calculations
"""

# BSD 3-Clause License
#
# Copyright (c) 2022-2026, Haju Schulz (haju.schulz@online.de)
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
    """Configuration data for arbitrary CRCs.

    Attributes:
        poly: Generator polynomial to use in the CRC calculation. The bits in
            this integer are the coefficients in the polynomial.
        width: Number of bits for the CRC calculation. Must match the
            generator polynomial.
        init: Seed value for the CRC calculation.
        revin: Reflect each single input byte if True.
        revout: Reflect the final CRC value if True.
        xor: Xor the final result with the value 0xff before returning it.
        access: Access size when swapping (8, 16, 32 or 64).
        swap: Swap bytes according to access size if True.
    """
    poly: int = 0x04C11DB7
    width: int = 32
    init: int = 0xFFFFFFFF
    revin: bool = True
    revout: bool = True
    xor: bool = True
    access: int = 8
    swap: bool = False

    def __str__(self) -> str:
        return \
            f"polynomial:0x{self.poly:X}, {self.width} Bit, "\
            f"init:0x{self.init:X}, "\
            f"reverse in:{self.revin}, reverse out:{self.revout}, "\
            f"final xor:{self.xor}, " \
            f"access:{self.access}, swap:{self.swap}"


class Crc:
    """Checksum processing."""

    def __init__(self, cfg: CrcConfig) -> None:
        """Create a Crc instance.

        Args:
            cfg: Configuration of the CRC algorithm.
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

    def __str__(self) -> str:
        return f"{self.cfg}"

    def checksum(self, data: bytearray) -> int:
        """Calculate the CRC checksum over given bytes.

        Args:
            data: Input bytes to check-sum.

        Returns:
            The computed CRC checksum.
        """

        return self.calculator.checksum(data)

    @staticmethod
    def _swap_access_16bit(data: bytearray) -> bytearray:
        """Byte-swap data in 16 bit chunks."""

        result = bytearray()
        for i in range(0, len(data), 2):
            result.extend(struct.pack(">H", struct.unpack("<H", data[i:i + 2])[0]))

        return result

    @staticmethod
    def _swap_access_32bit(data: bytearray) -> bytearray:
        """Byte-swap data in 32 bit chunks."""

        result = bytearray()
        for i in range(0, len(data), 4):
            result.extend(struct.pack(">I", struct.unpack("<I", data[i:i + 4])[0]))

        return result

    @staticmethod
    def _swap_access_64bit(data: bytearray) -> bytearray:
        """Byte-swap data in 64 bit chunks."""

        result = bytearray()
        for i in range(0, len(data), 8):
            result.extend(struct.pack(">Q", struct.unpack("<Q", data[i:i + 8])[0]))

        return result

    def prepare(self, data: bytearray) -> bytearray:
        """Convert a byte stream to match the access method from configuration.

        Args:
            data: Input byte array; must be a multiple of the access size long.

        Returns:
            The reordered bytearray.
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
