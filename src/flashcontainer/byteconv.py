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
from lxml.etree import DocumentInvalid
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
            raise DocumentInvalid(f"unsupported json value type {variant}")

        return result

    @staticmethod
    def fill_struct_from_json(strct: DM.Datastruct, input_str: str,
                               endianess: DM.Endianness, blockfill: int) -> bytearray:
        """Parse values for the structs field from JSON input"""

        # check for invalid input
        input_dict = json5.loads(input_str)
        if not isinstance(input_dict, dict):
            raise DocumentInvalid(f"Invalid input for struct:\n{input_str}")
        if not set(strct.get_field_names()) == set(input_dict.keys()):
            raise DocumentInvalid(f"struct {strct.name} field names and input keys are not equal")

        data = bytearray()
        for component in strct.fields:
            if isinstance(component, DM.Padding):
                if strct.filloption == "parent":
                    data.extend(bytearray((blockfill for _ in range(component.size))))
                else:
                    data.extend(bytearray((strct.filloption for _ in range(component.size))))
                continue
            fmt = "<" if endianess == DM.Endianness.LE else ">"
            fmt += DM.TYPE_DATA[component.type].fmt
            if isinstance(component, DM.Field):
                data.extend(bytearray(struct.pack(fmt, input_dict[component.name])))
            elif isinstance(component, DM.ArrayField):
                # check input validity for array
                ain = input_dict[component.name]
                if not isinstance(ain, list):
                    raise DocumentInvalid(f"Invalid input for struct:\n{input_str}")
                if len(ain) != component.count:
                    raise DocumentInvalid(f"ArrayField {component.name} of size {component.count}\
                                           supplied with {len(ain)} values.")
                for input_val in ain:
                    data.extend(bytearray(struct.pack(fmt, input_val)))
            else:  # crc
                calculator = DM.Crc(component.cfg)
                buffer = calculator.prepare(data.copy())
                crc_input = buffer[component.start: component.end + 1]
                checksum = calculator.checksum(crc_input)

                fmt = f"<{DM.TYPE_DATA[component.type].fmt}" if endianess == DM.Endianness.LE \
                    else f">{DM.TYPE_DATA[component.type].fmt}"

                byte_checksum = struct.pack(fmt, checksum)
                data.extend(byte_checksum)

        return data

    @staticmethod
    def value_to_c(value: int, type_data: DM.TypeData) -> str:
        """Convert single value to valid C"""
        if isinstance(value, float):
            return f"{value:>{type_data.width}.8f}"
        if isinstance(value, bytes):
            return f"0x{value.hex().upper()}"
        if type_data.signed:
            return f"{value:>{type_data.width}}"
        return f"0x{value:0{2*type_data.size}X}"

    @staticmethod
    def bytes_to_c_init(ptype: DM.ParamType, endianess: DM.Endianness, data: bytearray) -> str:
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

            result += ByteConvert.value_to_c(val, type_data)

            if i < (entries-1):
                result += ', '
                if 3 == (i % 4):
                    result += "\n    "

        if 1 < entries:
            result += "\n}"

        return result

    @staticmethod
    def struct_to_c_init(param: DM.Parameter, endianess: DM.Endianness) -> str:
        """Get the data for the fields (reverse of fill_strct_from_json()) and parse as a C var init"""
        strct = param.datastruct
        data_idx = 0
        result = "{"

        for field in strct.fields:
            result += "\n    "
            data = param.value[data_idx: data_idx + field.get_size()]
            data_idx += field.get_size()

            if isinstance(field, (DM.Padding, DM.ArrayField)):
                type_data = DM.TYPE_DATA[field.type] if isinstance(field, DM.ArrayField) else\
                      DM.TYPE_DATA[DM.ParamType.UINT8]
                fmt = "<" if endianess == DM.Endianness.LE else ">"
                if isinstance(field, DM.Padding):
                    fmt += type_data.fmt * field.get_size()
                else:
                    fmt += type_data.fmt * field.count
                values = struct.unpack(fmt, data)
                result += "{"
                for i, val in enumerate(values):
                    result += ByteConvert.value_to_c(val, type_data)
                    if i < len(values)-1:
                        result += ', '
                result += "},"

            if isinstance(field, (DM.Field, DM.CrcField)):
                fmt = "<" if endianess == DM.Endianness.LE else ">"
                fmt += DM.TYPE_DATA[field.type].fmt
                value = struct.unpack(fmt, data)[0]
                result += ByteConvert.value_to_c(value, DM.TYPE_DATA[field.type]) + ","

        result += "\n}"
        return result
