""" Internal datamodel for pargen
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

from __future__ import annotations

import logging
import struct
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from operator import attrgetter
from typing import Any, Dict, List, NamedTuple, Optional, TextIO, Union

from .checksum import Crc, CrcConfig

logger = logging.getLogger(__name__)

class CrcData(NamedTuple):
    """Configuration data for a single CRC parameter.

    Attributes:
        crc_cfg: CRC algorithm configuration.
        start: Address to start computation from.
        end: End address to stop computation at.
    """
    crc_cfg: CrcConfig = CrcConfig()
    start: int = 0
    end: int = 0

    def __str__(self) -> str:
        return f"0x{self.start:X}-0x{self.end:X}  {self.crc_cfg}"


@dataclass
class Version:
    """Version number data type."""

    major: int
    minor: int
    version: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.version}"

@dataclass
class BlockHeader:
    """Parameter block header container."""

    block_id: int
    version: Version


class Endianness(Enum):
    """Byte ordering."""

    LE = 1    # little endian (like x86)
    BE = 2    # big endian (like Motorola 68k)


class Block: # pylint: disable=too-many-instance-attributes
    """Block data container."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        addr: int, name: str,
        length: int, endianess: Endianness, fill: int) -> None:
        """Construct a block.

        Args:
            addr: Address of the block.
            name: The name of the block.
            length: The length of the block.
            endianess: The byte ordering of the block.
            fill: The fill value for gaps.
        """
        self.addr: int = addr
        self.name: str = name
        self.length: int = length
        self.header: Optional[BlockHeader] = None
        self.endianess: Endianness = endianess
        self.fill: int = fill & 0xFF
        self.parameter: List[Parameter] = []
        self.comment: Optional[str] = None

    def set_header(self, header: BlockHeader) -> None:
        """Add optional header data.

        Args:
            header: Header data to attach to this block.
        """
        self.header = header

    def add_parameter(self, parameter: Parameter) -> None:
        """Add a new parameter to the block.

        Args:
            parameter: Parameter to append.
        """
        self.parameter.append(parameter)

    def set_comment(self, comment: str) -> None:
        """Set an optional comment.

        Args:
            comment: Comment text.
        """

        self.comment = comment

    def get_header_bytes(self) -> bytes:
        """Get the block header as a byte stream.

        Returns:
            Packed header bytes.
        """

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
        """Insert a gap parameter at the given address.

        Args:
            addr: Start address of the gap.
            length: Length of the gap in bytes.
        """

        gap = Parameter.as_gap(addr, length, self.fill)
        logger.info("    Gap %s", gap)
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
        """Get the block data as a byte stream.

        Note:
            Content is only accurate if the block contains no gaps.

        Returns:
            Bytearray representing the block memory.
        """

        # build block raw data
        blk_bytes = bytearray()
        if self.header is not None:
            blk_bytes.extend(self.get_header_bytes())

        for param in self.parameter:
            blk_bytes.extend(param.value)

        return blk_bytes

    def update_crcs(self) -> None:
        """Compute CRC parameters inside the block.

        Note:
            Must be called after all parameters and fill gaps have been added.
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

            crcparam.value = bytearray(struct.pack(fmt, checksum))

            # patch crc into block memory to be considered in successive crcs
            slice_start = crcparam.offset - self.addr
            slice_end = slice_start + len(crcparam.value)
            blk_bytes[slice_start:slice_end] = crcparam.value

    def __str__(self) -> str:
        return f"Block({self.name} @ {hex(self.addr)})"


class ParamType(Enum):
    """Supported parameter data types."""
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
    """Parameter definition data container."""

    def __init__(self, # pylint: disable=too-many-arguments
            offset: int, name: Optional[str], ptype: ParamType,
            value: bytearray, crc: Optional[CrcData] = None) -> None:
        """Construct a parameter.

        Args:
            offset: Address of the parameter within its block.
            name: Parameter name, or None for gap fill parameters.
            ptype: Data type of the parameter.
            value: Raw byte value of the parameter.
            crc: CRC configuration if this is a CRC parameter.
        """
        self.offset: int = offset
        self.name: Optional[str] = name
        self.ptype: ParamType = ptype
        self.value: bytearray = value
        self.comment: Optional[str] = None
        self.crc_cfg: Optional[CrcData] = crc

    @classmethod
    def as_gap(cls, address: int, length: int, pattern: int) -> Parameter:
        """Create a parameter representing a gap fill range.

        Args:
            address: Gap start offset.
            length: Number of bytes in the gap area.
            pattern: Fill pattern for the gap (only the lowest 8 bits are used).

        Returns:
            Parameter object representing the gap.
        """
        val = bytearray([pattern & 0xFF] * length)
        return Parameter(address, None, ParamType.GAPFILL, val)

    def set_comment(self, comment: str) -> None:
        """Set an optional comment.

        Args:
            comment: Comment text.
        """
        self.comment = comment

    def __str__(self) -> str:
        return f"{self.name} @ {hex(self.offset)} = {self.value.hex()} "\
            f"len={len(self.value)}({hex(len(self.value))}) /* {self.comment } */"


class Container:
    """Data container holding a list of parameter blocks."""

    def __init__(self, name: str, addr: int) -> None:
        """Construct a container.

        Args:
            name: The name of the container.
            addr: Base address of the container.
        """
        self.name: str = name
        self.addr: int = addr
        self.blocks: List[Block] = []

    def add_block(self, block: Block) -> None:
        """Add a block to the container.

        Args:
            block: Block to append.
        """

        self.blocks.append(block)

    def __str__(self) -> str:
        return f"{self.name} @ {hex(self.addr)}"


class Model:
    """Top level model data container."""

    def __init__(self, name: Union[str, TextIO]) -> None:
        """Construct a model.

        Args:
            name: Name of the model, typically the source file or stream
                it was parsed from.
        """
        self.name: Union[str, TextIO] = name
        self.container: List[Container] = []

    def add_container(self, container: Container) -> None:
        """Append a container to the model.

        Args:
            container: Container to append.
        """

        self.container.append(container)

    def __str__(self) -> str:
        return f"Model({self.name} {self.container})"

    def validate(self, options: Dict[str, Any]) -> bool:
        """Validate the model.

        Args:
            options: Writer/validator context options.

        Returns:
            True if the model is valid, False otherwise.
        """

        validator = Validator(self, options)
        validator.run()

        return validator.result


class Walker:
    """A data model walker class.

    The run() method iterates the hierarchy of elements and calls begin/end
    methods for each element type. These methods are expected to be
    overwritten in derived classes for real processing.
    """

    def __init__(self, model: Model, options: Dict[str, Any]) -> None:
        """Construct a walker.

        Args:
            model: Data model to walk.
            options: Writer context options, made available to hooks.
        """
        self.options: Dict[str, Any] = options
        self.model: Model = model

        # current walking context
        self.ctx_container: Optional[Container] = None
        self.ctx_block: Optional[Block] = None
        self.ctx_parameter: Optional[Parameter] = None

    def pre_run(self) -> None:
        """Run actions before the model walk."""

    def post_run(self) -> None:
        """Run actions after the model walk."""

    def begin_container(self, container: Container) -> None:
        """Run actions when entering a container.

        Args:
            container: Container being entered.
        """

    def end_container(self, container: Container) -> None:
        """Run actions when leaving a container.

        Args:
            container: Container being left.
        """

    def begin_block(self, block: Block) -> None:
        """Run actions when entering a block.

        Args:
            block: Block being entered.
        """

    def end_block(self, block: Block) -> None:
        """Run actions when leaving a block.

        Args:
            block: Block being left.
        """

    def begin_parameter(self, param: Parameter) -> None:
        """Run begin actions for a parameter.

        Args:
            param: Parameter being visited.
        """

    def end_parameter(self, param: Parameter) -> None:
        """Run end actions for a parameter.

        Args:
            param: Parameter being visited.
        """

    def begin_gap(self, param: Parameter) -> None:
        """Run begin actions for a gap.

        Args:
            param: Gap parameter being visited.
        """

    def end_gap(self, param: Parameter) -> None:
        """Run end actions for a gap.

        Args:
            param: Gap parameter being visited.
        """

    def run(self) -> None:
        """Walk the data model."""

        self.pre_run()

        for container in self.model.container:
            self.ctx_container = container
            logger.debug("begin_container(%s)", container)
            self.begin_container(container)

            for block in container.blocks:
                self.ctx_block = block
                logger.debug("begin_block(%s)", block)

                self.begin_block(block)

                for parameter in block.parameter:
                    self.ctx_parameter = parameter

                    if ParamType.GAPFILL == parameter.ptype:
                        logger.debug("begin_gap(%s)", parameter)
                        self.begin_gap(parameter)
                        self.end_gap(parameter)
                        logger.debug("end_gap(%s)", parameter)

                    else:
                        logger.debug("begin_parameter(%s)", parameter)
                        self.begin_parameter(parameter)
                        self.end_parameter(parameter)
                        logger.debug("end_parameter(%s)", parameter)
                        self.ctx_parameter = None

                self.end_block(block)
                self.ctx_block = None
                logger.debug("end_block(%s)", block)

            self.end_container(container)
            self.ctx_container = None

            logger.debug("end_container(%s)", container)
        self.post_run()


class Validator(Walker):
    """Perform checks on the model to detect errors like overlapping parameters."""

    def __init__(self, model: Model, options: Dict[str, Any]) -> None:
        """Construct a validator.

        Args:
            model: Data model to validate.
            options: Writer context options, passed through to Walker.
        """
        super().__init__(model, options)
        self.result: bool = True
        self.last_param: Optional[Parameter] = None
        self.blocklist: Dict[str, Block] = {}
        self.paramlist: Dict[Optional[str], Parameter] = {}

    def begin_container(self, container: Container) -> None:
        self.blocklist = {}

    def begin_block(self, block: Block) -> None:
        self.last_param = None
        self.paramlist = {}

        if block.name in self.blocklist:
            self.error(
                f"block with name {block.name} already exists "
                f"@ 0x{self.blocklist[block.name].addr:08X}")
        else:
            self.blocklist[block.name] = block

    def begin_parameter(self, param: Parameter) -> None:

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
        """Issue an error message.

        Args:
            msg: Error message to print.
        """
        pfx = ""

        if self.ctx_container is not None:
            pfx += f"{self.ctx_container.name}:"

            if self.ctx_block is not None:
                pfx += f"{self.ctx_block.name}:"

        logger.error(f"{pfx}{msg}")

        self.result = False


# A tuple holding additional information for data model types
#
# fmt: format character used in struct.pack/unpack
# size: # of bytes used by one element of this type
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
