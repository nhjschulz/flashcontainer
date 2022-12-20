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

from enum import Enum
from typing import Dict, NamedTuple

import struct
import logging
import crc
from collections import namedtuple


class CrcConfig(NamedTuple):
    """Configuration data for arbitrary CRCs

        poly(int): Generator polynomial to use in the CRC calculation.
                   The bits in this integer are the coefficients in the polynomial.
        bit_width(int): Number of bits for the CRC calculation. They have to match with
                        the generator polynomial
        init(int): Seed value for the CRC calculation
        revin(bool): Reflect each single input byte if True
        revout(bool): Reflect the final CRC value if True
        xor(bool): Xor the final result with the value 0xff before returning the soulution
        start(int): Address to start computation from.
        end(int): End address to stop computation at.
    """
    poly: int = 0x04C11DB7
    width: int = 32
    init: int = 0xFFFFFFFF
    revin: bool = True
    revout: bool = True
    xor: bool = True
    start: int = 0
    end: int = 0

    def __str__(self):
        return f"0x{self.start:08X}-0x{self.end:08X} "\
            f"polynomial:0x{self.poly:08X}, {self.width} Bit, "\
            f"init: 0x{self.init:08X}, "\
            f"reverse in: {self.revin}, reverse out: {self.revout}, "\
            f"final xor: {self.xor}"


class Version:
    """Version number data type"""

    def __init__(self, major, minor, version):
        self.major = major
        self.minor = minor
        self.version = version

    def __print__(self):
        return f"{self.major}.{self.minor}.{self.version}"


class BlockHeader:
    """Parameter block header container """

    def __init__(self, id, version, length):
        self.id = id
        self.version = version
        self.length = length


class Endianness(Enum):
    """Byte ordering """

    LE = 1    # little endian (like x86)
    BE = 2    # big endian (like Motorola 68k)


class Block:
    """Block data container """

    def __init__(self, addr: int, name: str,  endianess: Endianness, fill: int):
        self.addr = addr
        self.name = name
        self.header = None
        self.endianess = endianess
        self.fill = fill & 0xFF
        self.parameter = []
        self.comment = None

    def set_header(self, header):
        self.header = header

    def add_parameter(self, parameter):
        self.parameter.append(parameter)

    def set_comment(self, comment: str) -> None:
        """Set optional comment"""

        self.comment = comment

    def get_header_bytes(self) -> bytearray:
        """Get header as bytestream."""

        fmt = "<" if self.endianess == Endianness.LE else ">"
        fmt += "HHHHII"

        return struct.pack(
            fmt,
            self.header.id,
            self.header.version.major,
            self.header.version.minor,
            self.header.version.version,
            0x00000000,
            self.header.length)

    def update_crc(self) -> None:
        """Add IEEE802.3 CRC32 at the end of the block as a parameter"""

        crcparams = []
        # build block raw data
        blk_bytes = bytearray()
        blk_bytes.extend(self.get_header_bytes())

        for param in self.parameter:
            blk_bytes.extend(param.value)
            if (param.crc_cfg is not None):
                crcparams.append(param)

        # compute each crc parameter value
        for crcparam in crcparams:
            cfg = crcparam.crc_cfg

            crc_calculator = crc.Calculator(
                crc.Configuration(
                    polynomial=cfg.poly, width=cfg.width,
                    init_value=cfg.init,
                    reverse_input=cfg.revin, reverse_output=cfg.revout,
                    final_xor_value=0 if cfg.xor is False else (0x1 << cfg.width)-1
                )
            )

            # update crc value in parameter structure
            start = cfg.start - self.addr
            end = start + (cfg.end - cfg.start)
            crc_input = blk_bytes[start:end]
            checksum = crc_calculator.checksum(crc_input)

            if self.endianess == Endianness.LE:
                fmt = f"<{TYPE_DATA[crcparam.type].fmt}"
            else:
                fmt = f">{TYPE_DATA[crcparam.type].fmt}"

            crcparam.value = struct.pack(fmt, checksum)

            # patch crc into block memory to be considered in successive crcs
            slice_start = crcparam.offset - self.addr
            slice_end = slice_start + len(crcparam.value)
            blk_bytes[slice_start:slice_end] = crcparam.value

    def __str__(self):
        return f"Block({self.name} @ {hex(self.addr)})"


class ParamType(Enum):
    uint32 = 1
    uint8 = 2
    uint16 = 3
    uint64 = 4
    int8 = 5
    int16 = 6
    int32 = 7
    int64 = 8
    float32 = 9
    float64 = 10
    utf8 = 11
    GAPFILL = 12


class Parameter:
    """Parameter definition data container"""

    def __init__(self, offset: int, name: str, type: ParamType, value: bytearray, crc: CrcConfig = None):
        self.offset = offset
        self.name = name
        self.type = type
        self.value = value
        self.comment = None
        self.crc_cfg = crc

    @classmethod
    def as_gap(cls, address: int, length: int, pattern: int):
        """Create parameter as a gap fill range with given pattern.

        Args:
            address (int): gap start offset
            length (int): Number of bytes in gap area
            pattern (int): Fill pattern for gap (only lowest 8bits used)

        Returns:
            Parameter object representing the gap
        """
        val = bytearray([pattern & 0xFF] * length)
        return Parameter(address, None, ParamType.GAPFILL, val)

    def set_comment(self, comment: str) -> None:
        """Set optional comment"""
        self.comment = comment

    def __str__(self):
        return f"{self.name} @ {hex(self.offset)} = {self.value.hex()} "\
            f"len={len(self.value)}({hex(len(self.value))}) /* {self.comment } */"


class Container:
    """Data container for a parameter block container"""

    def __init__(self, name, addr):
        self.name = name
        self.addr = addr
        self.blocks = []

    def add_block(self, block):
        self.blocks.append(block)

    def __str__(self):
        return f"{self.name} @ {hex(self.addr)}"


class Model:
    """Top level model data container"""

    def __init__(self, name):
        self.name = name
        self.container = []

    def add_container(self, container):
        self.container.append(container)

    def __str__(self):
        return f"Model({self.name} {self.container})"

    def validate(self, options: Dict[str, any]) -> bool:
        validator = Validator(self, options)
        validator.run()

        return validator.result


class Walker:
    """A data model walker class

    The run() method iterates the hierarchy of elements and
    calls begin/end methods for each element type. This methods
    are expected to be overwritten in derived classed for
    real processing.
    """

    def __init__(self, model: Model, options: Dict[str, any]):
        self.options = options
        self.model = model

        # current walking context
        self.ctx_container = None
        self.ctx_block = None
        self.ctx_parameter = None

    def pre_run(self):
        """Run actions before the model walk"""

        pass

    def post_run(self):
        """Run actions after the model walk"""

        pass

    def begin_container(self, container: Container) -> None:
        """Run actions when entering container """

        pass

    def end_container(self, container: Container) -> None:
        """Run actions when leaving container """

        pass

    def begin_block(self, block: Block) -> None:
        """Run actions when entering block """

        pass

    def end_block(self, block: Block) -> None:
        """Run actions when leaving block """

        pass

    def begin_parameter(self, param: Parameter) -> None:
        pass

    def end_parameter(self, param: Parameter) -> None:
        pass

    def begin_gap(self, param: Parameter) -> None:
        pass

    def end_gap(self, param: Parameter) -> None:
        pass

    def run(self):
        """Walk the data model."""

        self.pre_run()

        for container in self.model.container:
            self.ctx_container = container
            logging.debug(f"begin_container({container})")
            self.begin_container(container)

            for block in container.blocks:
                self.ctx_block = block
                logging.debug(f"begin_block({block})")

                self.begin_block(block)

                for parameter in block.parameter:
                    self.ctx_parameter = parameter

                    if ParamType.GAPFILL == parameter.type:
                        logging.debug(f"begin_gap({parameter})")
                        self.begin_gap(parameter)
                        self.end_gap(parameter)
                        logging.debug(f"end_gap({parameter})")

                    else:
                        logging.debug(f"begin_parameter({parameter})")
                        self.begin_parameter(parameter)
                        self.end_parameter(parameter)
                        logging.debug(f"end_parameter({parameter})")
                        self.ctx_parameter = None

                self.end_block(block)
                self.ctx_block = None
                logging.debug(f"end_block({block})")

            self.end_container(container)
            self.ctx_container = None

        logging.debug(f"end_container({container})")
        self.post_run()


class Validator(Walker):
    """Perform checks on the model to detect errors like overlapping parameter."""
    def __init__(self, model: Model, options: Dict[str, any]):
        super().__init__(model, options)
        self.result = True
        self.last_param = None

    def begin_block(self, block: Block):
        self.last_param = None

    def begin_parameter(self, param: Parameter):

        block_end = self.ctx_block.addr + self.ctx_block.header.length

        if param.offset > block_end:
            self.error(
                f" parameter {param.name} offset 0x{param.offset-self.ctx_block.addr:0X} is out of block range.")

        elif (param.offset + len(param.value)) > block_end:
            self.error(
                f" parameter '{param.name}' data exceeds block range by "
                f"{param.offset + len(param.value) - block_end} bytes.")

        if self.last_param is not None:
            end_last = self.last_param.offset + len(self.last_param.value)
            if (param.offset < end_last):

                self.error(
                    f" parameter '{param.name}' overlaps with '{self.last_param.name}'"
                    f" @ 0x{self.last_param.offset - self.ctx_block.addr:0X}.")

        self.last_param = param

    def error(self, msg: str) -> None:
        "issue error message"
        pfx = ""

        if self.ctx_container is not None:
            pfx += f"{self.ctx_container.name}:"

            if self.ctx_block is not None:
                pfx += f"{self.ctx_block.name}"

        logging.error(pfx + msg)

        self.result = False


# A tuple holding additional information for datamodel types
#
# fmt: format character used in struct.pack/unpack
# size: # if bytes used by one elemnent of this type
# witdh: preferned print width
# ctype: C-Language type
TypeData = namedtuple('TypeData', ['fmt', 'size', 'width', 'signed', 'ctype'])

TYPE_DATA = {
    ParamType.uint32:  TypeData("L", 4, 10, False, "uint32_t"),
    ParamType.uint8:   TypeData("B", 1, 4, False, "uint8_t"),
    ParamType.uint16:  TypeData("H", 2, 6, False, "uint16_t"),
    ParamType.uint64:  TypeData("Q", 8, 18, False, "uint64_t"),
    ParamType.int8:    TypeData("b", 1, 4, True, "int8_t"),
    ParamType.int16:   TypeData("h", 2, 6, True, "int16_t"),
    ParamType.int32:   TypeData("l", 4, 10, True, "int32_t"),
    ParamType.int64:   TypeData("q", 8, 16, True, "int64_t"),
    ParamType.float32: TypeData("f", 4, 12, True, "float"),
    ParamType.float64: TypeData("d", 8, 16, True, "double"),
    ParamType.utf8:    TypeData("1c", 1, 4, False, "char")
}
