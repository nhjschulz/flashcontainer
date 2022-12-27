"""XML Parser code for pargen."""
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

import logging
import pathlib
import os

import lxml.etree as ET

import flashcontainer.datamodel as DM
from flashcontainer.byteconv import ByteConvert
from flashcontainer.checksum import CrcConfig

schema_file = os.path.join(pathlib.Path(__file__).parent.resolve(), "pargen_1.0.xsd")
NS = '{http://nhjschulz.github.io/1.0/pargen}'


class XmlParser:
    """XML Parser to generate a datamodel from an XML file"""

    def __init__(self):
        pass

    @classmethod
    def from_file(cls, file: str) -> DM.Model:
        """Parser entry point returning model instance"""
        return cls.parse(file)

    @staticmethod
    def parse(file: str) -> DM.Model:
        """ Parse given XML file into datamodel. """
        model = None
        try:
            logging.info(f"Loading parameter definitons from {file}.")
            schema = ET.XMLSchema(ET.parse(schema_file))
            xml_doc = ET.parse(file)
            schema.assertValid(xml_doc)
            model = XmlParser._build_model(xml_doc.getroot(), file)

        except ET.DocumentInvalid as err:
            logging.critical(f"xml validation failed:\n{str(err.error_log)}") # pylint: disable=no-member
            return None


        return model

    @staticmethod
    def _get_optional(element: ET.Element, attr: str, default: any) -> str:
        """Get optional attribute value."""

        if element is None:
            return str(default)

        val = element.get(attr)
        if val is None:
            val = str(default)

        return val

    @staticmethod
    def _parse_bool(val_str: str) -> bool:
        """ Parse input as boolean """

        result = False
        if val_str is not None:
            val_str = val_str.lower()
            if ("true" == val_str) or ("1" == val_str):
                result = True

        return result

    @staticmethod
    def _parse_int(val_str: str) -> int:
        """ Parse int as decimal or hex."""

        try:
            return int(val_str, base=10)
        except ValueError:
            return int(val_str, base=16)

    @staticmethod
    def get_alignment(element: ET.Element) -> int:
        """Parse alignment argument."""

        val_str = element.get("align")
        return 1 if (val_str is None) else XmlParser._parse_int(val_str)

    @staticmethod
    def get_endianess(element: ET.Element) -> DM.Endianness:
        """Parse alignment argument."""

        val_str = element.get("endianness")
        if val_str is not None:
            return DM.Endianness.LE if val_str == "LE" else DM.Endianness.BE

        else:
            return DM.Endianness.LE

    @staticmethod
    def get_fill(element: ET.Element) -> int:
        """Parse fill argument."""

        val_str = element.get("fill")
        return 0x00 if (val_str is None) else XmlParser._parse_int(val_str)

    @staticmethod
    def _parse_crc_config(param: ET.Element, block: DM.Block, offset: int) -> DM.CrcConfig:
        """Parse a crc element.

        Args:
            param (ET.Element): The XML parameter element to read
            block (DM.Block): current block
            offset (int): offset of this parameter in block (used to resolve ".")

        Returns:
            A CrcConfig from the data model
        """

        mem_element = param.find(f"{NS}memory")
        cfg_element = param.find(f"{NS}config")

        defaults = CrcConfig()  # get defaults

        # parse cfg element
        width = DM.TYPE_DATA[DM.ParamType[param.get("type").upper()]].size * 8
        poly = XmlParser._parse_int(
            XmlParser._get_optional(cfg_element, 'polynomial', defaults.poly))
        init = XmlParser._parse_int(
            XmlParser._get_optional(cfg_element, 'init',  defaults.init))
        revin = XmlParser._parse_bool(
            XmlParser._get_optional(cfg_element, 'rev_in',  defaults.revin))
        revout = XmlParser._parse_bool(
            XmlParser._get_optional(cfg_element, 'rev_out',  defaults.revout))
        xor = XmlParser._parse_bool(
            XmlParser._get_optional(cfg_element, 'final_xor',  defaults.xor))

        # parse memory element
        start = XmlParser.calc_addr(
            block.addr,
            offset,
            XmlParser._get_optional(mem_element, "from", "0"),
            1)
        end = XmlParser.calc_addr(
            block.addr,
            offset,
            XmlParser._get_optional(mem_element, "to", "."),
            1)

        access = XmlParser._parse_int(
            XmlParser._get_optional(mem_element, 'access',  defaults.access))
        swap = XmlParser._parse_bool(XmlParser._get_optional(mem_element, 'swap',  defaults.swap))

        # special case for CRC: "." means end before current address, not at it.
        if "." == XmlParser._get_optional(mem_element, "to", "."):
            end = end - 1

        return DM.CrcData(
            crc_cfg=CrcConfig(
                poly=poly, width=width,
                init=init, revin=revin, revout=revout, xor=xor,
                access=access, swap=swap),
            start=start,
            end=end)

    @staticmethod
    def _build_parameters(block: DM.Block, element) -> None:
        data_element = element.find(f"{NS}data")
        running_addr = block.addr
        if block.header is not None:
            running_addr += len(block.get_header_bytes())

        for parameter_element in data_element:

            offset = XmlParser.calc_addr(
                block.addr,
                running_addr,
                parameter_element.get("offset"),
                XmlParser.get_alignment(parameter_element))

            name = parameter_element.get("name")
            ptype = DM.ParamType[parameter_element.get("type").upper()]
            crc_cfg = None
            val_text = None

            if f"{NS}crc" == parameter_element.tag:
                crc_cfg = XmlParser._parse_crc_config(parameter_element, block, offset)
                val_text = '0x0'  # crc bits get calculated at end of block
                logging.info("    got CRC data: %s", crc_cfg)
            else:
                value_element = parameter_element.find(f"{NS}value")
                val_text = value_element.text

            data = ByteConvert.json_to_bytes(ptype, block.endianess, val_text)

            parameter = DM.Parameter(offset, name, ptype, data, crc_cfg)

            comment = parameter_element.find(f"{NS}comment")
            if comment is not None:
                parameter.set_comment(comment.text)

            block.add_parameter(parameter)
            logging.info(f"    Adding {parameter}")
            running_addr = offset + len(data)

    @staticmethod
    def _build_model(root: ET.Element, filename: str) -> DM.Model:
        model = DM.Model(filename)

        # iterate over container list
        for element in root:
            address = XmlParser._parse_int(element.get("at"))
            name = element.get("name")

            container = DM.Container(name, address)
            logging.info(f"Loading container definition for {name}")
            XmlParser._build_blocks(container, element)

            model.add_container(container)

        return model

    @staticmethod
    def calc_addr(base_addr: int, running_addr: int, offset_str: str, alignment: int) -> int:
        """Calculate address from address input or '.'

        Args:
            base_addr(int): Start address of parent element
            running_addr(int): Next unused adderss in parent element
            offset_str(str): address information from XML
            alignment(int): optional address alignement to 1,2,4,8... boundary

        Returns:
            Aligned address if integer is passed or aligned next free address for '.'
        """

        if "." == offset_str:
            result_addr = running_addr

        else:
            result_addr = base_addr + XmlParser._parse_int(offset_str)

        if 1 < alignment:
            mod = result_addr % alignment
            if 0 != mod:
                result_addr += alignment - mod

        return result_addr

    @staticmethod
    def _build_blocks(container: DM.Container, element: ET.Element) -> None:
        """ Load block list for given container """

        running_addr = container.addr
        blocks_element = element.find(f"{NS}blocks")

        for element in blocks_element:
            align = XmlParser.get_alignment(element)
            block_addr = XmlParser.calc_addr(
                container.addr, running_addr, element.get("offset"), align)
            name = element.get("name")
            length = XmlParser._parse_int(element.get("length"))

            endianess = XmlParser.get_endianess(element)
            fill = XmlParser.get_fill(element)
            block = DM.Block(block_addr, name, length, endianess, fill)

            comment = element.find(f"{NS}comment")
            if comment is not None:
                block.set_comment(comment.text)

            logging.info(f"  Loading block definition {block}")

            # optional block header
            header_element = element.find(f"{NS}header")
            if header_element is not None:
                block_id = XmlParser._parse_int(header_element.get("id"))
                major = XmlParser._parse_int(header_element.get("major"))
                minor = XmlParser._parse_int(header_element.get("minor"))
                version = XmlParser._parse_int(header_element.get("version"))
                block.set_header(DM.BlockHeader(block_id, DM.Version(major, minor, version)))

            XmlParser._build_parameters(block, element)

            block.fill_gaps()
            block.update_crcs()
            container.add_block(block)

            running_addr += length
