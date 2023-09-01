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
from typing import Dict, NamedTuple, Optional, List
import struct
import logging
from collections import namedtuple
from operator import attrgetter
from dataclasses import dataclass
from itertools import chain
from abc import ABC, abstractmethod

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


@dataclass
class Version:
    """Version number data type"""

    major: int
    minor: int
    version: int

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.version}"

@dataclass
class BlockHeader:
    """Parameter block header container """

    block_id: int
    version: int


class Endianness(Enum):
    """Byte ordering """

    LE = 1    # little endian (like x86)
    BE = 2    # big endian (like Motorola 68k)


class Block:
    """Block data container """

    def __init__(
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


class BasicType(Enum):
    """Supported basic data types"""
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

class SpecialType(Enum):
    """Additional types for padding and structs"""
    GAPFILL = 12
    COMPLEX = 13

ParamType = Enum('ParamType', [(i.name, i.value) for i in chain(BasicType, SpecialType)])

class Parameter:
    """Parameter definition data container"""

    def __init__(self, # pylint: disable=too-many-arguments
            offset: int, name: str, ptype: ParamType,
            value: bytearray, crc: CrcData = None, datastruct: "Datastruct" = None):
        self.offset = offset
        self.name = name
        self.ptype = ptype
        self.value = value
        self.comment = None
        self.crc_cfg = crc
        self.datastruct = datastruct

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
        if self.datastruct is None:
            return f"{self.name} @ {hex(self.offset)} = {self.value.hex()} "\
                f"len={len(self.value)}({hex(len(self.value))}) /* {self.comment } */"
        return f"{self.name} @ {hex(self.offset)} of type {self.datastruct} "\
            f"/* {self.comment } */"


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
        self.datastructs = []

    def add_container(self, container):
        """Append container to model"""

        self.container.append(container)

    def add_struct(self, strct):
        """Append data struct to model"""
        self.datastructs.append(strct)

    def get_struct_by_name(self, name: str) -> Optional["Datastruct"]:
        """Resturns the struct with the given name if one is present"""
        candidates = [s for s in self.datastructs if s.name == name]
        return candidates[0] if candidates else None

    def __str__(self):
        return f"Model({self.name} {self.container})"

    def validate(self, options: Dict[str, any]) -> bool:
        """Validate model"""

        validator = Validator(self, options)
        validator.run()

        if validator.result is False:
            print("")

        return validator.result


@dataclass
class StructElement(ABC):
    """Base class for the components in a struct"""

    @abstractmethod
    def get_size(self) -> int:
        """Returns the size of the element in the struct"""


@dataclass
class Field(StructElement):
    """Field in a struct"""
    name: str
    type: BasicType
    comment: str = None

    def __post_init__(self):
        self.type = ParamType(self.type.value)

    def get_size(self) -> int:
        """Returns the size of the basic type and therefore the field"""
        return TYPE_DATA[self.type].size


@dataclass
class ArrayField(StructElement):
    """Field that holds multiple values of the same type"""
    name: str
    type: BasicType
    count: int
    comment: str = None

    def __post_init__(self):
        self.type = ParamType(self.type.value)

    def get_size(self) -> int:
        return TYPE_DATA[self.type].size * self.count


@dataclass
class Padding(StructElement):
    """Padding element to create gaps between Fields"""
    size: int

    def get_size(self) -> int:
        return self.size


@dataclass
class CrcField(StructElement):
    """Crc element to represent CRC in a struct"""
    name: str
    type: BasicType
    cfg: CrcConfig
    start: int
    end: int

    def __post_init__(self):
        self.type = ParamType(self.type.value)

    def get_size(self) -> int:
        return TYPE_DATA[self.type].size


class Datastruct:
    """ Class to hold struct type information """

    def __init__(self, name: str, filloption: str) -> None:
        self.name = name
        self.fields = []
        if filloption not in ("parent"):
            try:
                self.filloption = int(filloption) & 0xFF
            except ValueError:
                self.filloption = int(filloption, 16) & 0xFF
        else:
            self.filloption = filloption
        self.comment = None

    def set_comment(self, comment: str) -> None:
        """Set optional comment"""
        self.comment = comment

    def add_field(self, field: StructElement) -> None:
        """Add field to the data struct"""
        self.fields.append(field)

    def get_size(self) -> int:
        """Returns the size of all struct components combined"""
        return sum((f.get_size() for f in self.fields))

    def get_field_names(self, include_crcs: bool = False) -> List[str]:
        """Returns a list of all named fields names in the struct"""
        if include_crcs:
            return [f.name for f in self.fields if isinstance(f, (Field, ArrayField, CrcField))]
        return [f.name for f in self.fields if isinstance(f, (Field, ArrayField))]

    def __str__(self) -> str:
        """Return a string representation of the struct"""
        return f"{self.name} ({self.get_size()} bytes)"


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
        """Run begin actions for parameter"""

    def end_parameter(self, param: Parameter) -> None:
        """Run end actions for parameter"""

    def begin_gap(self, param: Parameter) -> None:
        """Run begin actions for gaps"""

    def end_gap(self, param: Parameter) -> None:
        """Run end actions for gaps"""

    def begin_struct(self, strct: Datastruct) -> None:
        """Run begin action for structs"""

    def end_struct(self, strct: Datastruct) -> None:
        """Run end action for structs"""

    def begin_field(self, field: Field) -> None:
        """Run begin action for fields"""

    def end_field(self, field: Field) -> None:
        """Run end action for fields"""

    def run(self):
        """Walk the data model."""

        self.pre_run()

        for strct in self.model.datastructs:
            logging.debug("begin_struct(%s)", strct)
            self.begin_struct(strct)

            for field in strct.fields:
                self.begin_field(field)
                self.end_field(field)

            self.end_struct(strct)

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
        self.blockdict = {}
        self.paramdict = {}
        self.structdict = {}
        self.fielddict = {}


    def begin_container(self, container: Container) -> None:
        self.blockdict = {}

    def begin_struct(self, strct: Datastruct) -> None:
        if strct.name in self.structdict:
            self.error(f"struct {strct.name} defined more than once in the model")
        self.structdict.update({strct.name: strct})
        self.fielddict = {}

    def begin_field(self, field: StructElement) -> None:
        if isinstance(field, (Field, ArrayField, CrcField)):
            if field.name in self.fielddict:
                self.error(f"field {field.name} defined more than once in the same struct")
            self.fielddict[field.name] = field

    def begin_block(self, block: Block):
        self.last_param = None
        self.paramdict = {}

        if block.name in self.blockdict:
            self.error(
                f"block with name {block.name} already exists "
                f"@ 0x{self.blockdict[block.name].addr:08X}")
        else:
            self.blockdict[block.name] = block

    def begin_parameter(self, param: Parameter):

        if param.name in self.paramdict:
            self.error(
                f"parameter with name {param.name} already exists "
                f"@ 0x{self.paramdict[param.name].offset:08X}")
        else:
            self.paramdict[param.name] = param

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
    ParamType.UTF8:    TypeData("1c", 1, 4, False, "char"),
}
