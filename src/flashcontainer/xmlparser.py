"""XML Parser code for pargen."""
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

import logging
import pathlib
import os
import re
from typing import Dict, Optional, Tuple

import lxml.etree as ET

import flashcontainer.datamodel as DM
from flashcontainer.byteconv import ByteConvert
from flashcontainer.checksum import CrcConfig




class XmlParser:
    """XML Parser to generate a datamodel from an XML file"""

    def __init__(self) -> None:
        self.pd_ns = 'http://nhjschulz.github.io/1.0/pargen'
        self.model = None

    @classmethod
    def from_file(cls, file: str, values: Dict[str, str] = None) -> Optional[DM.Model]:
        """Parser entry point returning model instance"""
        parser = XmlParser()
        return parser.parse(file, values)

    def parse(self, file: str, values: Dict[str, str]) -> Optional[DM.Model]:
        """ Parse given XML file into data model. """
        model = None

        namespaceregex = re.compile(r"http://nhjschulz.github.io/(\d+).(\d+)/pargen")
        try:
            preview = ET.parse(file, ET.XMLParser(remove_comments=True))
            try:
                searchresult = namespaceregex.search(preview.getroot().nsmap['pd'])
                major = searchresult.group(1)
                minor = searchresult.group(2)

                schema_filename = f"pargen_{major}.{minor}.xsd"
                schema_file = os.path.join(pathlib.Path(__file__).parent.resolve(), schema_filename)
                self.pd_ns = f'http://nhjschulz.github.io/{major}.{minor}/pargen'

            except  KeyError as exc:
                raise ET.DocumentInvalid("No pd namespace configured on root element.") from exc

            logging.info("Loading parameter definitions from %s.", file)
            schema = ET.XMLSchema(ET.parse(schema_file))
            xml_doc = ET.parse(file, ET.XMLParser(remove_comments=True))
            schema.assertValid(xml_doc)
            self._update_values(xml_doc.getroot(), values)
            model = self._build_model(xml_doc.getroot(), file)

        except ET.DocumentInvalid as err:
            logging.critical("xml validation failed:\n%s", str(err.error_log)) # pylint: disable=no-member
            return None


        return model

    def _update_values(self, root,  values: Dict[str, str]):
        """Update parameter values based on modifier list."""

        if values is not None:
            for param_name, param_value in list(values.items()):
                xpath = ET.XPath(
                    f"//pd:param[@name='{param_name}']/pd:value",
                    namespaces={'pd': self.pd_ns}
                )
                hits = xpath(root)
                if hits:
                    for element in hits:
                        element.text = param_value
                else:
                    logging.warning(
                        "Unable to modify parameter '%s': name is not defined.",
                         param_name)

    def _get_optional(self, element: ET.Element, attr: str, default: any) -> str:
        """Get optional attribute value."""

        if element is None:
            return str(default)

        val = element.get(attr)
        if val is None:
            val = str(default)

        return val

    def _parse_bool(self, val_str: str) -> bool:
        """ Parse input as boolean """

        result = False
        if val_str is not None:
            val_str = val_str.lower()
            if val_str in ('true', '1'):
                result = True

        return result

    def _parse_int(self, val_str: str) -> int:
        """ Parse int as decimal or hex."""

        try:
            return int(val_str, base=10)
        except ValueError:
            return int(val_str, base=16)

    def get_alignment(self, element: ET.Element) -> int:
        """Parse alignment argument."""

        val_str = element.get("align")
        return 1 if (val_str is None) else self._parse_int(val_str)

    def get_endianess(self, element: ET.Element) -> DM.Endianness:
        """Parse alignment argument."""

        val_str = self._get_optional(element, "endianness", "LE")
        return DM.Endianness.LE if val_str == "LE" else DM.Endianness.BE

    def get_fill(self, element: ET.Element) -> int:
        """Parse fill argument."""

        val_str = element.get("fill")
        return 0x00 if (val_str is None) else self._parse_int(val_str)

    def _parse_crc_config(self, param: ET.Element) -> Tuple[int, int, int, bool, bool, bool]:
        """Parse the configuration of a crc parameter or field"""
        cfg_element = param.find(f"{{{self.pd_ns}}}config")

        defaults = CrcConfig()  # get defaults

        # parse cfg element
        width = DM.TYPE_DATA[DM.ParamType[param.get("type").upper()]].size * 8
        poly = self._parse_int(
            self._get_optional(cfg_element, 'polynomial', defaults.poly))
        init = self._parse_int(
            self._get_optional(cfg_element, 'init',  defaults.init))
        revin = self._parse_bool(
            self._get_optional(cfg_element, 'rev_in',  defaults.revin))
        revout = self._parse_bool(
            self._get_optional(cfg_element, 'rev_out',  defaults.revout))
        xor = self._parse_bool(
            self._get_optional(cfg_element, 'final_xor',  defaults.xor))
        return (poly, width, init, revin, revout, xor)

    def _parse_crc_memory(self, param: ET.Element,
                            offset: int,
                            block: Optional[DM.Block] = None) -> Tuple[int, int, int, bool]:
        """Parse the memory tag of a crc parameter or field"""
        mem_element = param.find(f"{{{self.pd_ns}}}memory")
        if block is not None:
            start = self.calc_addr(
                block.addr,
                offset,
                self._get_optional(mem_element, "from", "0"),
                1)
            end = self.calc_addr(
                block.addr,
                offset,
                self._get_optional(mem_element, "to", "."),
                1)
        else:
            start = self.calc_addr(0x0, offset, self._get_optional(mem_element, "from", "0"), 1)
            end = self.calc_addr(0x0, offset, self._get_optional(mem_element, "to", "."), 1)

        defaults = CrcConfig()  # get defaults
        access = self._parse_int(
            self._get_optional(mem_element, 'access',  defaults.access))
        swap = self._parse_bool(self._get_optional(mem_element, 'swap',  defaults.swap))

        # special case for CRC: "." means end before current address, not at it.
        if "." == self._get_optional(mem_element, "to", "."):
            end = end - 1

        return (start, end, access, swap)

    def _parse_crc_param(self, param: ET.Element, block: DM.Block, offset: int) -> DM.CrcConfig:
        """Parse a crc parameter.

        Args:
            param (ET.Element): The XML parameter element to read
            block (DM.Block): current block
            offset (int): offset of this parameter in block (used to resolve ".")

        Returns:
            A CrcConfig from the data model
        """

        poly, width, init, revin, revout, xor = self._parse_crc_config(param)
        start, end, access, swap = self._parse_crc_memory(param, offset, block=block)

        return DM.CrcData(
            crc_cfg=CrcConfig(
                poly=poly, width=width,
                init=init, revin=revin, revout=revout, xor=xor,
                access=access, swap=swap),
            start=start,
            end=end)

    def _build_parameters(self, block: DM.Block, element: ET.Element) -> None:
        running_addr = block.addr
        if block.header is not None:
            running_addr += len(block.get_header_bytes())

        for parameter_element in element.find(f"{{{self.pd_ns}}}data"):

            offset = self.calc_addr(
                block.addr,
                running_addr,
                parameter_element.get("offset"),
                self.get_alignment(parameter_element))
            ptype = DM.ParamType[parameter_element.get("type").upper()]
            crc_cfg = None
            val_text = None

            if f"{{{self.pd_ns}}}crc" == parameter_element.tag:
                crc_cfg = self._parse_crc_param(parameter_element, block, offset)
                val_text = '0x0'  # crc bits get calculated at end of block
                logging.info("    got CRC data: %s", crc_cfg)
            else:
                value_element = parameter_element.find(f"{{{self.pd_ns}}}value")
                val_text = value_element.text

            if ptype == DM.ParamType.COMPLEX:
                # get the corresponding struct object
                sname = parameter_element.get("struct")
                if sname is None:
                    logging.critical("Parsing complex parameter with no struct attribute")
                    raise ET.DocumentInvalid("Parsing complex parameter with no struct attribute")
                if self.model.datastructs is None or sname not in [s.name for s in self.model.datastructs]:
                    logging.critical("Parsing complex parameter with undefined struct name")
                    raise ET.DocumentInvalid("Parsing complex parameter with undefined struct name")
                strct = [s for s in self.model.datastructs if s.name == sname][0]

                data = ByteConvert.fill_struct_from_json(strct, val_text, block.endianess, block.fill)
                parameter = DM.Parameter(offset, parameter_element.get("name"), ptype, data, crc_cfg, datastruct=strct)
            else:
                data = ByteConvert.json_to_bytes(ptype, block.endianess, val_text)
                parameter = DM.Parameter(offset, parameter_element.get("name"), ptype, data, crc_cfg)

            comment = parameter_element.find(f"{{{self.pd_ns}}}comment")
            if comment is not None:
                parameter.set_comment(comment.text)

            block.add_parameter(parameter)
            logging.info("    Adding %s", parameter)
            running_addr = offset + len(data)

    def _build_model(self, root: ET.Element, filename: str) -> DM.Model:
        self.model = DM.Model(filename)

        # iterate over structs and containers
        for element in root:
            if element.tag == f"{{{self.pd_ns}}}container":
                address = self._parse_int(element.get("at"))
                name = element.get("name")

                container = DM.Container(name, address)
                logging.info("Loading container definition for %s", name)
                self._build_blocks(container, element)

                self.model.add_container(container)
            elif element.tag == f"{{{self.pd_ns}}}struct":
                name = element.get("name")
                filloption = element.get("fill")
                logging.info("Found struct with name %s and filloption %s!", name, filloption)

                strct = DM.Datastruct(name, filloption)
                self._build_struct(strct, element)
                self.model.add_struct(strct)

        return self.model

    def calc_addr(self, base_addr: int, running_addr: int, offset_str: str, alignment: int) -> int:
        """Calculate address from address input or '.'

        Args:
            base_addr(int): Start address of parent element
            running_addr(int): Next unused address in parent element
            offset_str(str): address information from XML
            alignment(int): optional address alignment to 1,2,4,8... boundary

        Returns:
            Aligned address if integer is passed or aligned next free address for '.'
        """

        if "." == offset_str:
            result_addr = running_addr

        else:
            result_addr = base_addr + self._parse_int(offset_str)

        if 1 < alignment:
            mod = result_addr % alignment
            if 0 != mod:
                result_addr += alignment - mod

        return result_addr

    def _build_blocks(self, container: DM.Container, xml_element: ET.Element) -> None:
        """ Load block list for given container """

        running_addr = container.addr

        for element in xml_element.find(f"{{{self.pd_ns}}}blocks"):
            block_addr = self.calc_addr(
                container.addr, running_addr, element.get("offset"), self.get_alignment(element))
            name = element.get("name")
            length = self._parse_int(element.get("length"))

            endianess = self.get_endianess(element)
            fill = self.get_fill(element)
            block = DM.Block(block_addr, name, length, endianess, fill)

            comment = element.find(f"{{{self.pd_ns}}}comment")
            if comment is not None:
                block.set_comment(comment.text)

            logging.info("  Loading block definition %s", block)

            # optional block header
            header_element = element.find(f"{{{self.pd_ns}}}header")
            if header_element is not None:
                block_id = self._parse_int(header_element.get("id"))
                version = DM.Version(
                    self._parse_int(header_element.get("major")),
                    self._parse_int(header_element.get("minor")),
                    self._parse_int(header_element.get("version"))
                )
                block.set_header(DM.BlockHeader(block_id, version))

            self._build_parameters(block, element)

            block.fill_gaps()
            block.update_crcs()
            container.add_block(block)

            running_addr += length

    def _build_struct(self, strct: DM.Datastruct, xml_element: ET.Element) -> None:
        """ Parse the fields of a data structure"""
        strct_comment = xml_element.find(f"{{{self.pd_ns}}}comment")
        if strct_comment is not None:
            strct.set_comment(strct_comment.text)

        for element in xml_element.find(f"{{{self.pd_ns}}}fields"):
            if element.tag in (f"{{{self.pd_ns}}}field",
                                f"{{{self.pd_ns}}}arrayfield",
                                  f"{{{self.pd_ns}}}crc"):
                name = element.get("name")
                btype = DM.BasicType[element.get("type").upper()]
                comment = None
                field_comment = element.find(f"{{{self.pd_ns}}}comment")
                if field_comment is not None:
                    comment = field_comment.text
                if element.tag == f"{{{self.pd_ns}}}arrayfield":
                    count = self._parse_int(element.get("size"))
                    field = DM.ArrayField(name, btype, count, comment=comment)
                elif element.tag == f"{{{self.pd_ns}}}field":
                    field = DM.Field(name, btype, comment=comment)
                else:  # crcfield
                    cfargs = self._parse_crc_config(element)
                    start, end, access, swap = self._parse_crc_memory(element, strct.get_size())
                    field = DM.CrcField(name, btype, CrcConfig(*cfargs, access, swap), start, end)
                strct.add_field(field)
            elif element.tag == f"{{{self.pd_ns}}}padding":
                strct.add_field(DM.Padding(self._parse_int(element.get("size"))))
