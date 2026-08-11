"""XML Parser code for pargen."""
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

import logging
import os
import pathlib
from typing import Any, Dict, List, Optional, TextIO, Union

import lxml.etree as ET

from . import datamodel as DM
from .byteconv import ByteConvert
from .checksum import CrcConfig

schema_file = os.path.join(pathlib.Path(__file__).parent.resolve(), "pargen_1.0.xsd")
NS = 'http://nhjschulz.github.io/1.0/pargen'

logger = logging.getLogger(__name__)


class IncludeResolver(ET.Resolver):
    """Custom XML resolver for XInclude that searches additional include dirs."""

    def __init__(self, include_dirs: Optional[List[str]] = None):
        super().__init__()
        self.include_dirs = include_dirs or []

    def resolve(self, system_url: str, public_id: str, context) -> Any:
        candidate_names = [system_url]
        if os.path.isabs(system_url):
            candidate_names.append(os.path.basename(system_url))
        else:
            candidate_names.append(os.path.basename(system_url))

        for include_dir in self.include_dirs:
            for name in candidate_names:
                candidate = os.path.join(include_dir, name)
                if os.path.exists(candidate):
                    return self.resolve_filename(candidate, context)
        return None


class XmlParser:
    """XML parser to generate a data model from an XML file."""

    @classmethod
    def from_file(
        cls, file: Union[str, TextIO], values: Optional[Dict[str, str]] = None,
        include_dirs: Optional[List[str]] = None
    ) -> Optional[DM.Model]:
        """Parser entry point returning a model instance.

        Args:
            file: Path to the XML file, or an open file-like object.
            values: Optional map of parameter name to override value.

        Returns:
            The parsed data model, or None if parsing failed.
        """
        return cls.parse(file, values, include_dirs)

    @staticmethod
    def parse(file: Union[str, TextIO], values: Optional[Dict[str, str]],
              include_dirs: Optional[List[str]] = None) -> Optional[DM.Model]:
        """Parse the given XML file into a data model.

        Args:
            file: Path to the XML file, or an open file-like object.
            values: Optional map of parameter name to override value.

        Returns:
            The parsed data model, or None if XML schema validation failed.
        """
        model = None
        try:
            logger.info("Loading parameter definitions from %s.", file)
            schema = ET.XMLSchema(ET.parse(schema_file))

            parser = ET.XMLParser(remove_comments=True)
            if include_dirs:
                parser.resolvers.add(IncludeResolver(include_dirs))

            xml_doc = ET.parse(file, parser)
            xml_doc.xinclude()

            XmlParser._flatten_included_pargen(xml_doc.getroot())
            schema.assertValid(xml_doc)
            XmlParser._update_values(xml_doc.getroot(), values)
            model = XmlParser._build_model(xml_doc.getroot(), file)

        except ET.XIncludeError as err:
            logger.critical("xml XInclude failed: %s", err)
            return None
        except ET.DocumentInvalid as err:
            logger.critical("xml validation failed:\n%s", str(err.error_log)) # pylint: disable=no-member
            return None


        return model

    @staticmethod
    def _flatten_included_pargen(root: ET.Element) -> None:
        """Flatten included <pargen> root elements inserted by XInclude."""
        for child in list(root):
            if child.tag == f"{{{NS}}}pargen":
                insertion_index = root.index(child)
                for grandchild in list(child):
                    root.insert(insertion_index, grandchild)
                    insertion_index += 1
                root.remove(child)
            else:
                XmlParser._flatten_included_pargen(child)

    @staticmethod
    def _update_values(root: ET.Element, values: Optional[Dict[str, str]]) -> None:
        """Update parameter values in the XML tree based on a modifier list.

        Args:
            root: Root element of the XML document to update in place.
            values: Optional map of parameter name to override value.
        """

        if values is not None:
            for param_name, param_value in list(values.items()):
                xpath = ET.XPath(
                    f"//pd:param[@name='{param_name}']/pd:value",
                    namespaces={'pd': NS}
                )
                hits = xpath(root)
                if hits:
                    for element in hits:
                        element.text = param_value
                else:
                    logger.warning(
                        "Unable to modify parameter '%s': name is not defined.",
                        param_name,
                    )

    @staticmethod
    def _get_optional(element: ET.Element, attr: str, default: Any) -> str:
        """Get an optional attribute value, falling back to a default.

        Args:
            element: XML element to read the attribute from, may be None.
            attr: Name of the attribute to read.
            default: Value to return if element or the attribute is missing.

        Returns:
            The attribute value, or the string representation of default.
        """

        if element is None:
            return str(default)

        val = element.get(attr)
        if val is None:
            val = str(default)

        return val

    @staticmethod
    def _parse_bool(val_str: str) -> bool:
        """Parse input as a boolean.

        Args:
            val_str: Input string, e.g. "true" or "1" for True.

        Returns:
            True if val_str represents a true value, False otherwise
            (including when val_str is None).
        """

        result = False
        if val_str is not None:
            val_str = val_str.lower()
            if val_str in ('true', '1'):
                result = True

        return result

    @staticmethod
    def _parse_int(val_str: str) -> int:
        """Parse an integer as decimal or hex.

        Args:
            val_str: Input string, e.g. "42" or "0x2A".

        Returns:
            The parsed integer value.
        """

        try:
            return int(val_str, base=10)
        except ValueError:
            return int(val_str, base=16)

    @staticmethod
    def get_alignment(element: ET.Element) -> int:
        """Parse the alignment attribute of an XML element.

        Args:
            element: XML element that may carry an "align" attribute.

        Returns:
            The alignment value, or 1 if not specified.
        """

        val_str = element.get("align")
        return 1 if (val_str is None) else XmlParser._parse_int(val_str)

    @staticmethod
    def get_endianess(element: ET.Element) -> DM.Endianness:
        """Parse the endianness attribute of an XML element.

        Args:
            element: XML element that may carry an "endianness" attribute.

        Returns:
            The parsed Endianness, defaulting to little endian.
        """

        val_str = XmlParser._get_optional(element, "endianness", "LE")
        return DM.Endianness.LE if val_str == "LE" else DM.Endianness.BE

    @staticmethod
    def get_fill(element: ET.Element) -> int:
        """Parse the fill attribute of an XML element.

        Args:
            element: XML element that may carry a "fill" attribute.

        Returns:
            The fill byte value, or 0x00 if not specified.
        """

        val_str = element.get("fill")
        return 0x00 if (val_str is None) else XmlParser._parse_int(val_str)

    @staticmethod
    def _parse_crc_config(param: ET.Element, block: DM.Block, offset: int) -> DM.CrcData:
        """Parse a crc element.

        Args:
            param: The XML crc parameter element to read.
            block: Block the crc parameter belongs to.
            offset: Offset of this parameter in the block (used to resolve ".").

        Returns:
            CRC configuration data parsed from param.
        """

        mem_element = param.find(f"{{{NS}}}memory")
        cfg_element = param.find(f"{{{NS}}}config")

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
    def _build_parameters(block: DM.Block, element: ET.Element) -> None:
        """Parse and add all parameters of a block element to the block.

        Args:
            block: Block to add the parsed parameters to.
            element: XML block element containing the parameter data.
        """

        data_element = element.find(f"{{{NS}}}data")
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

            if f"{{{NS}}}crc" == parameter_element.tag:
                crc_cfg = XmlParser._parse_crc_config(parameter_element, block, offset)
                val_text = '0x0'  # crc bits get calculated at end of block
                logger.info("    got CRC data: %s", crc_cfg)
            else:
                value_element = parameter_element.find(f"{{{NS}}}value")
                val_text = value_element.text

            data = ByteConvert.json_to_bytes(ptype, block.endianess, val_text)

            parameter = DM.Parameter(offset, name, ptype, data, crc_cfg)

            comment = parameter_element.find(f"{{{NS}}}comment")
            if comment is not None:
                parameter.set_comment(comment.text)

            block.add_parameter(parameter)
            logger.info("    Adding %s", parameter)
            running_addr = offset + len(data)

    @staticmethod
    def _build_model(root: ET.Element, filename: Union[str, TextIO]) -> DM.Model:
        """Build a data model from the root element of an XML document.

        Args:
            root: Root element of the parsed XML document.
            filename: Source of the XML document, used as the model name.

        Returns:
            The resulting data model.
        """

        model = DM.Model(filename)

        # iterate over container list
        for element in root:
            address = XmlParser._parse_int(element.get("at"))
            name = element.get("name")

            container = DM.Container(name, address)
            logger.info("Loading container definition for %s", name)
            XmlParser._build_blocks(container, element)

            model.add_container(container)

        return model

    @staticmethod
    def calc_addr(base_addr: int, running_addr: int, offset_str: str, alignment: int) -> int:
        """Calculate an address from an address string or '.'.

        Args:
            base_addr: Start address of the parent element.
            running_addr: Next unused address in the parent element.
            offset_str: Address information from XML, or "." for the next
                free address.
            alignment: Address alignment to a 1, 2, 4, 8... byte boundary.

        Returns:
            The aligned address if an integer was passed, or the aligned
            next free address for '.'.
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
    def _build_blocks(container: DM.Container, xml_element: ET.Element) -> None:
        """Load the block list for a given container.

        Args:
            container: Container to add the parsed blocks to.
            xml_element: XML container element holding the block definitions.
        """

        running_addr = container.addr
        blocks_element = xml_element.find(f"{{{NS}}}blocks")

        for element in blocks_element:
            align = XmlParser.get_alignment(element)
            block_addr = XmlParser.calc_addr(
                container.addr, running_addr, element.get("offset"), align)
            name = element.get("name")
            length = XmlParser._parse_int(element.get("length"))

            endianess = XmlParser.get_endianess(element)
            fill = XmlParser.get_fill(element)
            block = DM.Block(block_addr, name, length, endianess, fill)

            comment = element.find(f"{{{NS}}}comment")
            if comment is not None:
                block.set_comment(comment.text)

            logger.info("  Loading block definition %s", block)

            # optional block header
            header_element = element.find(f"{{{NS}}}header")
            if header_element is not None:
                block_id = XmlParser._parse_int(header_element.get("id"))
                version = DM.Version(
                    XmlParser._parse_int(header_element.get("major")),
                    XmlParser._parse_int(header_element.get("minor")),
                    XmlParser._parse_int(header_element.get("version"))
                )
                block.set_header(DM.BlockHeader(block_id, version))

            XmlParser._build_parameters(block, element)

            block.fill_gaps()
            block.update_crcs()
            container.add_block(block)

            running_addr += length
