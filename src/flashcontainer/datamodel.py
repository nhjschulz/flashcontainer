""" Internal datamodel for pargen
"""
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

from enum import Enum
from typing import Dict, NamedTuple
import struct
import logging
from collections import namedtuple
from operator import attrgetter

from flashcontainer.checksum import Crc, CrcConfig


class CrcData(NamedTuple):
    """Configuration data for arbitrary CRCs

        crc_cfg: Crc configuration data
        start(int): Address to start computation from.
        end(int): End address to stop computation at.
    """
    crc_cfg: CrcConfig = CrcConfig()
    start: int = 0
    end: int = 0

    def __str__(self):
        return f"0x{self.start:X}-0x{self.end:X}  {self.crc_cfg}"


class Version:  # pylint: disable=too-few-public-methods
    """Version number data type"""

    def __init__(self, major, minor, version):
        self.major = major
        self.minor = minor
        self.version = version

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.version}"


class BlockHeader:  # pylint: disable=too-few-public-methods
    """Parameter block header container """

    def __init__(self, block_id, version):
        self.block_id = block_id
        self.version = version


class Endianness(Enum):
    """Byte ordering """

    LE = 1    # little endian (like x86)
    BE = 2    # big endian (like Motorola 68k)


class Block: # pylint: disable=too-many-instance-attributes
    """Block data container """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        addr: int, name: str,
        length: int, endianess: Endianness, fill: int):
        """ Construct a block.

            Args:
                addr(int): address of the block
                name(str): the name of the block
                length(int): the length of the block
                endianess(Endianess): the byte ordering of the block
                fill(int:) the fill value for gaps
        """
        self.addr = addr
        self.name = name
        self.length = length
        self.header = None
        self.endianess = endianess
        self.fill = fill & 0xFF
        self.parameter = []
        self.comment = None

    def set_header(self, header):
        """ Add optional header data
        """
        self.header = header

    def add_parameter(self, parameter):
        """ Add new parmeter to block.
        """
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
            self.header.block_id,
            self.header.version.major,
            self.header.version.minor,
            self.header.version.version,
            0x00000000,
            self.length)

    def _insert_gap(self, addr: int, length: int) -> None:
        """Insert a gap at address of with len bytes.

        Args:
            addr(int): start address of gap
            len(int): length of gap
        """

        gap = Parameter.as_gap(addr, length, self.fill)
        logging.info("    Gap %s", gap)
        self.add_parameter(gap)

    def fill_gaps(self) -> None:
        """Insert gap parameter between the parameters."""

        # sort parameter by address
        param_list = sorted(self.parameter, key=attrgetter('offset'))

        running_addr = self.addr
        if self.header is not None:
            running_addr += len(self.get_header_bytes())

        for param in param_list:
            if param.offset > running_addr:   # we need to insert a gap
                self._insert_gap(running_addr, param.offset - running_addr)

            running_addr = param.offset + len(param.value)

        # tail gap at end of block needed ?
        end_addr = self.addr + self.length
        if end_addr > running_addr:  # we need to insert a gap at the end
            self._insert_gap(running_addr, end_addr - running_addr)

        self.parameter = sorted(self.parameter, key=attrgetter('offset'))

    def get_bytes(self) -> bytearray:
        """Get the block data as byte stream

            Note: Contant is only accurate if block contains
                  no gaps.

            Returns:
                bytearray representing the block memory
        """

        # build block raw data
        blk_bytes = bytearray()
        if self.header is not None:
            blk_bytes.extend(self.get_header_bytes())

        for param in self.parameter:
            blk_bytes.extend(param.value)

        return blk_bytes

    def update_crcs(self) -> None:
        """Compute crc parameters inside the block.

        Must be called after all parameters and
        fill gaps got added.
        """

        blk_bytes = self.get_bytes()

        # compute each crc parameter value
        for crcparam in self.parameter:
            if crcparam.crc_cfg is None:
                continue

            cfg = crcparam.crc_cfg
            crc_calculator = Crc(cfg.crc_cfg)

            # update buffer in case of byte swapped 16/32/64 bit access
            buffer = crc_calculator.prepare(blk_bytes)

            # update crc value in parameter structure
            start = cfg.start - self.addr
            end = start + (cfg.end - cfg.start)
            crc_input = buffer[start:end+1]
            checksum = crc_calculator.checksum(crc_input)

            if self.endianess == Endianness.LE:
                fmt = f"<{TYPE_DATA[crcparam.ptype].fmt}"
            else:
                fmt = f">{TYPE_DATA[crcparam.ptype].fmt}"

            crcparam.value = struct.pack(fmt, checksum)

            # patch crc into block memory to be considered in successive crcs
            slice_start = crcparam.offset - self.addr
            slice_end = slice_start + len(crcparam.value)
            blk_bytes[slice_start:slice_end] = crcparam.value

    def __str__(self):
        return f"Block({self.name} @ {hex(self.addr)})"


class ParamType(Enum):
    """Supported data types"""
    UINT32 = 1
    UINT8 = 2
    UINT16 = 3
    UINT64 = 4
    INT8 = 5
    INT16 = 6
    INT32 = 7
    INT64 = 8
    FLOAT32 = 9
    FLOAT64 = 10
    UTF8 = 11
    GAPFILL = 12


class Parameter:
    """Parameter definition data container"""

    def __init__(self, # pylint: disable=too-many-arguments
            offset: int, name: str, ptype: ParamType,
            value: bytearray, crc: CrcData = None):
        self.offset = offset
        self.name = name
        self.ptype = ptype
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
        """Add a block to the container"""

        self.blocks.append(block)

    def __str__(self):
        return f"{self.name} @ {hex(self.addr)}"


class Model:
    """Top level model data container"""

    def __init__(self, name):
        self.name = name
        self.container = []

    def add_container(self, container):
        """Append container to model"""

        self.container.append(container)

    def __str__(self):
        return f"Model({self.name} {self.container})"

    def validate(self, options: Dict[str, any]) -> bool:
        """Validate model"""

        validator = Validator(self, options)
        validator.run()

        if validator.result is False:
            print("")

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

    def post_run(self):
        """Run actions after the model walk"""

    def begin_container(self, container: Container) -> None:
        """Run actions when entering container """

    def end_container(self, container: Container) -> None:
        """Run actions when leaving container """

    def begin_block(self, block: Block) -> None:
        """Run actions when entering block """

    def end_block(self, block: Block) -> None:
        """Run actions when leaving block """

    def begin_parameter(self, param: Parameter) -> None:
        """ Run begin actions for parameter"""

    def end_parameter(self, param: Parameter) -> None:
        """ Run end actions for parameter"""

    def begin_gap(self, param: Parameter) -> None:
        """ Run begin actions for gaps"""

    def end_gap(self, param: Parameter) -> None:
        """ Run end actions for gaps"""

    def run(self):
        """Walk the data model."""

        self.pre_run()

        for container in self.model.container:
            self.ctx_container = container
            logging.debug("begin_container(%s)", container)
            self.begin_container(container)

            for block in container.blocks:
                self.ctx_block = block
                logging.debug("begin_block(%s)", block)

                self.begin_block(block)

                for parameter in block.parameter:
                    self.ctx_parameter = parameter

                    if ParamType.GAPFILL == parameter.ptype:
                        logging.debug("begin_gap(%s)", parameter)
                        self.begin_gap(parameter)
                        self.end_gap(parameter)
                        logging.debug("end_gap(%s)", parameter)

                    else:
                        logging.debug("begin_parameter(%s)", parameter)
                        self.begin_parameter(parameter)
                        self.end_parameter(parameter)
                        logging.debug("end_parameter(%s)", parameter)
                        self.ctx_parameter = None

                self.end_block(block)
                self.ctx_block = None
                logging.debug("end_block(%s)", block)

            self.end_container(container)
            self.ctx_container = None

            logging.debug("end_container(%s)", container)
        self.post_run()


class Validator(Walker):
    """Perform checks on the model to detect errors like overlapping parameter."""
    def __init__(self, model: Model, options: Dict[str, any]):
        super().__init__(model, options)
        self.result = True
        self.last_param = None
        self.blocklist = {}
        self.paramlist = {}

    def begin_container(self, container: Container) -> None:
        self.blocklist = {}

    def begin_block(self, block: Block):
        self.last_param = None
        self.paramlist = {}

        if block.name in self.blocklist:
            self.error(
                f"block with name {block.name} already exists "
                f"@ 0x{self.blocklist[block.name].addr:08X}")
        else:
            self.blocklist[block.name] = block

    def begin_parameter(self, param: Parameter):

        if param.name in self.paramlist:
            self.error(
                f"parameter with name {param.name} already exists "
                f"@ 0x{self.paramlist[param.name].offset:08X}")
        else:
            self.paramlist[param.name] = param

        block_end = self.ctx_block.addr + self.ctx_block.length

        if param.offset >= block_end:
            self.error(
                f" parameter {param.name} offset 0x{param.offset-self.ctx_block.addr:0X} "\
                "is out of block range.")

        elif (param.offset + len(param.value)) > block_end:
            self.error(
                f" parameter '{param.name}' data exceeds block range by "
                f"{param.offset + len(param.value) - block_end} bytes.")

        if self.last_param is not None:
            end_last = self.last_param.offset + len(self.last_param.value)
            if param.offset < end_last:
                self.error(
                    f" parameter '{param.name}' overlaps with '{self.last_param.name}'"
                    f" @ 0x{self.last_param.offset - self.ctx_block.addr:0X}.")

        if self.ctx_block.header is not None:
            min_addr = self.ctx_block.addr + len(self.ctx_block.get_header_bytes())
            if param.offset < min_addr:
                self.error(
                    f" parameter '{param.name}' overlaps with block header.")

        self.last_param = param

    def end_container(self, container: Container) -> None:

        # sort parameter by address and check for overlaps.
        sorted_blocks = sorted(container.blocks, key=attrgetter('addr'))
        prev = None
        for block in sorted_blocks:
            if prev is not None:
                prev_end = prev.addr + prev.length

                if block.addr < prev_end:
                    self.error(
                        f"block {prev.name} overlaps with block "
                        f"{block.name} @ 0x{block.addr:X}")
            prev = block

    def error(self, msg: str) -> None:
        """
        Issue error message.

        Args:
            msg(str): error message to print
        """
        pfx = ""

        if self.ctx_container is not None:
            pfx += f"{self.ctx_container.name}:"

            if self.ctx_block is not None:
                pfx += f"{self.ctx_block.name}:"

        logging.error(pfx + msg)

        self.result = False


# A tuple holding additional information for data model types
#
# fmt: format character used in struct.pack/unpack
# size: # if bytes used by one element of this type
# width: preferred print width
# ctype: C-Language type
TypeData = namedtuple('TypeData', ['fmt', 'size', 'width', 'signed', 'ctype'])

TYPE_DATA = {
    ParamType.UINT32:  TypeData("L", 4, 10, False, "uint32_t"),
    ParamType.UINT8:   TypeData("B", 1, 4, False, "uint8_t"),
    ParamType.UINT16:  TypeData("H", 2, 6, False, "uint16_t"),
    ParamType.UINT64:  TypeData("Q", 8, 18, False, "uint64_t"),
    ParamType.INT8:    TypeData("b", 1, 4, True, "int8_t"),
    ParamType.INT16:   TypeData("h", 2, 6, True, "int16_t"),
    ParamType.INT32:   TypeData("l", 4, 10, True, "int32_t"),
    ParamType.INT64:   TypeData("q", 8, 16, True, "int64_t"),
    ParamType.FLOAT32: TypeData("f", 4, 12, True, "float"),
    ParamType.FLOAT64: TypeData("d", 8, 16, True, "double"),
    ParamType.UTF8:    TypeData("1c", 1, 4, False, "char")
}
