"""Write configuraton file for pyHexDump"""
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

import json5

import flashcontainer.datamodel as DM
from flashcontainer.byteconv import ByteConvert

# Header data types
_HEADER_STRUCTURES = [
    {
        "name": "pargen_header_le_t",
        "elements":
        [
            {
                "name": "id",
                "dataType": "uint16le",
                "count": 1
            },
            {
                "name": "major",
                "dataType": "uint16le",
                "count": 1
            },
            {
                "name": "minor",
                "dataType": "uint16le",
                "count": 1
            },
            {
                "name": "dataver",
                "dataType": "uint16le",
                "count": 1
            },
            {
                "name": "reserved",
                "dataType": "uint32le",
                "count": 1
            },
            {
                "name": "length",
                "dataType": "uint32le",
                "count": 1
            }
        ]
    },
    {
        "name": "pargen_header_be_t",
        "elements":
        [
            {
                "name": "id",
                "dataType": "uint16be",
                "count": 1
            },
            {
                "name": "major",
                "dataType": "uint16be",
                "count": 1
            },
            {
                "name": "minor",
                "dataType": "uint16be",
                "count": 1
            },
            {
                "name": "dataver",
                "dataType": "uint16be",
                "count": 1
            },
            {
                "name": "reserved",
                "dataType": "uint32be",
                "count": 1
            },
            {
                "name": "length",
                "dataType": "uint32be",
                "count": 1
            }
        ]
    }
]


class PyHexDumpWriter(DM.Walker):
    """Create configuration file for pyHexDump (see https://github.com/BlueAndi/pyHexDump) """

    _TYPE_MAPPING = {
        DM.ParamType.UINT8: ("uint8", "uint8"),
        DM.ParamType.UINT16: ("uint16le", "uint16be"),
        DM.ParamType.UINT32: ("uint32le", "uint32be"),
        DM.ParamType.UINT64: ("uint64le", "uint64be"),
        DM.ParamType.INT8: ("int8", "int8"),
        DM.ParamType.INT16: ("int16le", "int16be"),
        DM.ParamType.INT32: ("int32le", "int32be"),
        DM.ParamType.INT64: ("int64le", "int64be"),
        DM.ParamType.FLOAT32: ("float32le", "float32be"),
        DM.ParamType.FLOAT64: ("float64le", "float64be"),
        DM.ParamType.UTF8: ("utf8", "utf8")
    }

    def __init__(self, model: DM.Model, options: Dict[str, any]):
        super().__init__(model, options)
        self.dmpfile = None
        self.elements = []
        self.definded_structs = []

    def pre_run(self) -> None:
        filename = Path.joinpath(
            self.options.get("DESTDIR"),
            self.options.get("BASENAME") + ".pyhexdump")

        print(f"Generating pyHexDump config file {filename}.")

        self.dmpfile = filename.open(mode='w')

    def begin_block(self, block: DM.Block) -> None:
        """Add header if present"""

        if block.header is not None:

            subtype = "le" if self.ctx_block.endianess == DM.Endianness.LE else "be"

            element = {
                "name": f"{self.ctx_block.name}_blkhdr",
                "addr": f"{hex(block.addr)}",
                "dataType": f"pargen_header_{subtype}_t",
                "count": 1
            }

            self.elements.append(element)

    def begin_parameter(self, param: DM.Parameter) -> None:
        """Add element to data array """
        if param.ptype != DM.ParamType.COMPLEX:
            element = {
                "name": f"{param.name}",
                "addr": f"{hex(param.offset)}",
                "dataType": self._TYPE_MAPPING[param.ptype]
                    [0 if self.ctx_block.endianess == DM.Endianness.LE else 1],
                "count": len(param.value) // ByteConvert.get_type_size(param.ptype)
            }
        else:
            element = {
                "name": f"{param.name}",
                "addr": f"{hex(param.offset)}",
                "dataType": f"pargen_{param.datastruct.name}_" + \
                    f"{'le' if self.ctx_block.endianess == DM.Endianness.LE else 'be'}_t",
                "count": 1
            }

        self.elements.append(element)

    def begin_struct(self, strct: DM.Datastruct) -> None:
        """Add BE and LE versions of the struct to the defined structures"""
        structure_dicts = ({ "name": f"pargen_{strct.name}_le_t", "elements": []},
                            { "name": f"pargen_{strct.name}_be_t", "elements": []})

        for i, _ in enumerate(("le", "be")):
            offset = 0
            offset_needed = False
            for field in strct.fields:
                if isinstance(field, (DM.Field, DM.ArrayField, DM.CrcField)):
                    element = {
                        "name": f"{field.name}",
                        "dataType": self._TYPE_MAPPING[field.type][i],
                        "count": field.count if isinstance(field, DM.ArrayField) else 1
                    }
                    if offset_needed:
                        element.update({"offset": offset})
                        offset_needed = False
                    offset += field.get_size()
                    structure_dicts[i]["elements"].append(element)
                else:
                    # padding requires no entry but correct offset for next element
                    offset += field.get_size()
                    offset_needed = True

        self.definded_structs.extend(structure_dicts)

    def post_run(self):
        """Close output file"""

        comment = [
            "Configuration file for pyHexDump, see https://github.com/BlueAndi/pyHexDump",
            f"GENERATED by {self.options.get('PNAME')} {self.options.get('VERSION')} ",
            f"cmd: {self.options.get('CMDLINE')}"
        ]

        if self.options.get("STATICOUTPUT") is False:
            comment.append(f"date: {self.options.get('DATETIME')}")
            comment.append(f"Buildkey: {self.options.get('GUID')}")

        record = {
            "_comment_": comment,
            "structures": _HEADER_STRUCTURES + self.definded_structs,
            "elements": self.elements
            }

        json_str = json5.dumps(record, quote_keys=True, indent=4, trailing_commas=False)
        self.dmpfile.write(json_str)
        self.dmpfile.close()
