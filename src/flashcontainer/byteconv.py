
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

import json5
import struct

#  Map model types to struct formats
_STRUCT_FMTS = {
    DM.ParamType.uint32: "L",
    DM.ParamType.uint8: "B",
    DM.ParamType.uint16: "H",
    DM.ParamType.uint64: "Q",
    DM.ParamType.int8: "b",
    DM.ParamType.int16: "h",
    DM.ParamType.int32: "l",
    DM.ParamType.int64: "q",
    DM.ParamType.float32: "f",
    DM.ParamType.float64: "d",
    DM.ParamType.utf8: "1c"
}

#  Map model types to sizeof() in bytes
_SIZE_MAPPING = {
    DM.ParamType.uint32: 4,
    DM.ParamType.uint8: 1,
    DM.ParamType.uint16: 2,
    DM.ParamType.uint64: 8,
    DM.ParamType.int8: 1,
    DM.ParamType.int16: 2,
    DM.ParamType.int32: 4,
    DM.ParamType.int64: 8,
    DM.ParamType.float32: 4,
    DM.ParamType.float64: 8,
    DM.ParamType.utf8: 1,
}


class ByteConvert:
    def __init__(self):
        pass

    @staticmethod
    def get_type_size(ptype: DM.ParamType) -> int:
        """Get bytesize of type"""

        return _SIZE_MAPPING.get(ptype)

    @staticmethod
    def json_to_bytes(ptype: DM.ParamType,  endianess: DM.Endianness, value_str: str) -> bytearray:
        """Convert from json string into raw bytes """

        result = bytearray()
        from_json = json5.loads(value_str)
        variant = type(from_json)
        fmt = "<" if endianess == DM.Endianness.LE else ">"
        fmt += _STRUCT_FMTS[ptype]

        if (variant == list):  # == array
            for i in range(0, len(from_json)):
                result.extend(struct.pack(fmt, from_json[i]))

        elif (variant in [int, float]):
            result.extend(bytearray(struct.pack(fmt, from_json)))

        elif (variant == str):
            enc_utf8 = 'utf-8'
            utf8_bytes = bytes(from_json, enc_utf8)
            result.extend(struct.pack(f"<{len(utf8_bytes)}s", utf8_bytes))
            result.extend(b'\x00')

        else:
            raise Exception(f"unsupported json value type {variant}")

        return result

    def bytes_to_c_init(ptype: DM.ParamType,  endianess: DM.Endianness, data: bytearray) -> str:
        """Convert raw data to C-Language initializer"""

        result = ""
        item_size = ByteConvert.get_type_size(ptype)
        fmt = "<" if endianess == DM.Endianness.LE else ">"
        fmt += _STRUCT_FMTS[ptype] * (len(data) // item_size)

        values = struct.unpack(fmt, data)
        entries = len(values)
        if 1 < entries:
            result += "\n{\n    "

        for i in range(0, entries):
            val = values[i]

            if (isinstance(val, float)):
                result += f"{val:.8f}"
            elif (isinstance(val, bytes)):
                result += f"0x{val.hex().upper()}"
            else:
                result += f"0x{val:0X}"

            if i < (entries-1):
                result += ', '
                if 3 == (i % 4):
                    result += "\n    "

        if 1 < entries:
            result += "\n}"

        return result
