""" Conversions between byte arrays and text
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

import struct
import json5

import flashcontainer.datamodel as DM

class ByteConvert:
    """Byte to Text conversions
    """

    @staticmethod
    def get_type_size(ptype: DM.ParamType) -> int:
        """Get byte size of type"""

        return DM.TYPE_DATA[ptype].size

    @staticmethod
    def json_to_bytes(ptype: DM.ParamType,  endianess: DM.Endianness, value_str: str) -> bytearray:
        """Convert from json string into raw bytes """

        result = bytearray()
        from_json = json5.loads(value_str)
        variant = type(from_json)
        fmt = "<" if endianess == DM.Endianness.LE else ">"
        fmt += DM.TYPE_DATA[ptype].fmt

        if variant == list:  # == array
            for array_item in from_json:
                result.extend(struct.pack(fmt, array_item))

        elif variant in [int, float]:
            result.extend(bytearray(struct.pack(fmt, from_json)))

        elif variant == str:
            enc_utf8 = 'utf-8'
            utf8_bytes = bytes(from_json, enc_utf8)
            result.extend(struct.pack(f"<{len(utf8_bytes)}s", utf8_bytes))
            result.extend(b'\x00')

        else:
            raise Exception(f"unsupported json value type {variant}") # pylint: disable=broad-except

        return result

    @staticmethod
    def bytes_to_c_init(ptype: DM.ParamType,  endianess: DM.Endianness, data: bytearray) -> str:
        """Convert raw data to C-Language initializer"""

        result = ""
        type_data = DM.TYPE_DATA[ptype]
        item_size = type_data.size
        fmt = "<" if endianess == DM.Endianness.LE else ">"
        fmt += type_data.fmt * (len(data) // item_size)

        values = struct.unpack(fmt, data)
        entries = len(values)
        if 1 < entries:
            result += "\n{\n    "

        for i in range(0, entries):
            val = values[i]

            if isinstance(val, float):
                result += f"{val:>{type_data.width}.8f}"
            elif isinstance(val, bytes):
                result += f"0x{val.hex().upper()}"
            else:
                if type_data.signed:
                    result += f"{val:>{type_data.width}}"
                else:
                    result += f"0x{val:0{2*type_data.size}X}"

            if i < (entries-1):
                result += ', '
                if 3 == (i % 4):
                    result += "\n    "

        if 1 < entries:
            result += "\n}"

        return result
