""" Alternate boot mode header generation for TC3XX processors
"""

# BSD 3-Clause License
#
# Copyright (c) 2023, Haju Schulz (haju.schulz@online.de)
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

import argparse
import pathlib
import os
import sys
import textwrap
import logging
from enum import Enum
from pathlib import Path

from intelhex import IntelHex
import lxml.etree as ET

from flashcontainer.packageinfo import __version__
from flashcontainer.tc3xx_cmd import Tc3xxCmdBase
from flashcontainer.checksum import Crc, CrcConfig

class RETVAL(Enum):
    """abmhd CLI error codes """

    OK = 0
    FILE_NOT_FOUND = 1
    INVALID_FORMAT = 2
    VALIDATION_FAIL = 3
    INVALID_PARAMETER = 4


class Tc3xxAbmhd(Tc3xxCmdBase):
    """Implementation of abmhd command"""

    # XML definition template for alternate boot mode header
    _abmhd_xml = os.path.join(
        pathlib.Path(__file__).parent.resolve(), "tc3xx_abmhd.xml")

    # valid header ID value
    _abmhd_ok_id =  0xFA7CB359

    def __init__(self) -> None:
        """Init this module and register abmhd command with the Tc3xx CLI"""

        self.min_addr  = 0x0
        self.max_addr  = 0x0
        self.stad_addr = 0x0
        self.hdr_id = 0x0
        self.user_crc = 0x0

        self.input_hex_file = ""
        self.input_hex_data = IntelHex()

        self.abmhd_addr = 0x0
        self.output = sys.stdout

    @staticmethod
    def _static_run(args) -> int:
        """Non class wrapper to call run method from argparser."""

        return Tc3xxAbmhd().run(args)

    def register(self, sub_parsers) -> None:
        """Register abmhd command arguments with the Tc3xx CLI"""

        parser = sub_parsers.add_parser(
            'abmhd',
            help='Generate alternate boot mode header',
            formatter_class=argparse.RawTextHelpFormatter,
            description=
            """Generate TC3XX alternate boot mode header Pargen definition file.\n\n"""
            """Example:\n"""
            """    tc3xx abmhd --stad 0x80028000 --from 0x8002000 --to 0x8004000  0x80000100 fw.hex | """
            """pargen --ihex -f abmhd -""" )

        parser.add_argument(
            "--stad", "-s", nargs=1,
            type=lambda x: int(x,0),
            metavar="STADABM",
            help='user code start address (default: lowest address in hexfile)'
        )
        parser.add_argument(
            "--from", "-f", nargs=1,
            type=lambda x: int(x,0),
            dest='chk_from',
            metavar="CHKSTART",
            help='begin of range to be checked (default: lowest address in hexfile)'
        )
        parser.add_argument(
            "--to", "-t", nargs=1,
            type=lambda x: int(x,0),
            dest='chk_to',
            metavar="CHKEND",
            help='end of range to be checked (default: highest address in hexfile + 1)'
        )

        parser.add_argument(
            "--abmhdid", "-i", nargs=1,
            type=lambda x: int(x,0),
            metavar="ABMHDID",
            default=0xFA7CB359,
            help=f'alternate Boot Mode Header Identifier value (default=0x{Tc3xxAbmhd._abmhd_ok_id:X})'
        )

        parser.add_argument(
            "--output", "-o", nargs=1,
            metavar="filename",
            help='file name of generated Pargen xml file (default: <stdout>)'
        )

        parser.add_argument(
            'address',
            nargs=1,
            metavar='ADDRESS',
            type=lambda x: int(x,0),
            help='flash address of alternate boot mode header.')

        parser.add_argument(
            'filename',
            metavar='HEXFILE',
            nargs=1,
            help='name of hexfile with user data content')

        parser.set_defaults(func=Tc3xxAbmhd._static_run)


    def run(self, args) -> int:
        """abmhd command executer"""

        result = self._evaluate_arguments(args)
        if RETVAL.OK.value == result:
            result = self._validate()
            if RETVAL.OK.value == result:
                self._calc_user_data_crc()
                pargen_xml = self._generate_xml()

                if self.output == sys.stdout:
                    self.output.write(pargen_xml)
                else:
                    with open(self.output, 'w', encoding='utf-8') as outfile:
                        outfile.write(pargen_xml)

        return result

    def _evaluate_arguments(self, args) -> int:
        """Convert argument values to class context variables."""

        # check input hexfile argument
        self.input_hex_file = args.filename[0]
        if not Path(self.input_hex_file).is_file():
            logging.error("file not found: %s", self.input_hex_file)
            return RETVAL.FILE_NOT_FOUND.value

        logging.info("Loading user data from %s", self.input_hex_file)
        try:
            self.input_hex_data.loadhex(self.input_hex_file)
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception(exc, stack_info=False, exc_info=False)
            return RETVAL.INVALID_FORMAT.value
        logging.info (
            "User Data Range: 0x%08X - 0x%08X",
            self.input_hex_data.minaddr(),
            self.input_hex_data.maxaddr()
        )

        self.min_addr = args.chk_from[0] if args.chk_from is not None else self.input_hex_data.minaddr()
        self.max_addr = args.chk_to[0]if args.chk_to is not None else self.input_hex_data.maxaddr() + 1
        self.stad_addr = args.stad[0] if args.stad is not None else self.min_addr
        self.hdr_id = args.abmhdid if args.abmhdid is not None else Tc3xxAbmhd._abmhd_ok_id

        if args.output is not None:
            self.output = str(Path(args.output[0]))

        self.abmhd_addr = args.address[0]

        return RETVAL.OK.value

    def _validate(self) -> int:
        """Check correctness of received input"""

        result = RETVAL.OK.value

        # Validate  check address range information
        if (self.min_addr < self.input_hex_data.minaddr()) or (self.min_addr >= self.input_hex_data.maxaddr()):
            logging.error(
                "check start address 0x%08x out of user data range 0x%08x - 0x%08x",
                self.min_addr,
                self.input_hex_data.minaddr(),
                self.input_hex_data.maxaddr()
            )
            result =  RETVAL.INVALID_PARAMETER.value

        if (self.max_addr < self.input_hex_data.minaddr()) or (self.max_addr > (self.input_hex_data.maxaddr() + 1)):
            logging.error(
                "check end address 0x%08x out of user data range 0x%08x - 0x%08x",
                self.min_addr,
                self.input_hex_data.minaddr(),
                self.input_hex_data.maxaddr()
            )
            result =  RETVAL.INVALID_PARAMETER.value

        if self.max_addr < self.min_addr:
            logging.error(
                "invalid check data range 0x%08x - 0x%08x",
                self.min_addr,
                self.max_addr
            )
            result =  RETVAL.INVALID_PARAMETER.value

        #validate start address
        if (self.stad_addr < self.input_hex_data.minaddr()) or (self.stad_addr > (self.input_hex_data.maxaddr())):
            logging.error(
                "user code start address 0x%08x out of user data range 0x%08x - 0x%08x",
                self.stad_addr,
                self.input_hex_data.minaddr(),
                self.input_hex_data.maxaddr()
            )
            result =  RETVAL.INVALID_PARAMETER.value

        if 0 != (self.stad_addr & 0x3):
            logging.error("user code start address 0x%08x must be WORD aligned", self.stad_addr)
            result =  RETVAL.INVALID_PARAMETER.value

        if 0 != (self.min_addr & 0x3):
            logging.error("check start address 0x%08x must be WORD aligned", self.stad_addr)
            result =  RETVAL.INVALID_PARAMETER.value

        if 0 != (self.max_addr & 0x3):
            logging.error("check end address 0x%08x must be WORD aligned", self.stad_addr)
            result =  RETVAL.INVALID_PARAMETER.value

        return result

    def _calc_user_data_crc(self):
        """Build CRC value over user data."""

        logging.info("Calculating CRC from 0x%0x-0x%0x", self.min_addr, self.max_addr)

        user_data = bytearray()

        for address in range (self.min_addr, self.max_addr):
            user_data.append(self.input_hex_data[address])

        crc_cfg = CrcConfig(
                poly=0x04C11DB7, width=32,
                init=0xFFFFFFFF, revin=True, revout=True, xor=True,
                access=32, swap=True)
        crc_calculator = Crc(crc_cfg)
        self.user_crc = crc_calculator.checksum(crc_calculator.prepare(user_data))

    def _generate_xml(self) -> str:
        """Generate Pargen definition XML"""

        dest = self.output if self.output != sys.stdout else "<stdout>"
        logging.info("Writing Pargen XML definition into %s", dest)
        xml_dom = ET.fromstring(
            self._get_xml(),
            ET.XMLParser(remove_blank_text=True, encoding='utf-8')
        )
        etree = ET.ElementTree(xml_dom)
        ET.indent(etree, "    ")

        return '<?xml version="1.0" encoding="utf-8"?>\n'+ ET.tounicode(etree, pretty_print=True)

    def _get_xml(self) -> str:
        """Get resulting XML record as string"""

        return textwrap.dedent(f'''\
            <?xml version="1.0" encoding="utf-8"?>
            <!--
                Flashcontainer configuration for Aurix TC3xx alternate boot mode header
                Autogenerated by tc3xx {__version__} for {self.input_hex_file}
            -->
            <pd:pargen xmlns:pd="http://nhjschulz.github.io/1.0/pargen"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xsi:schemaLocation="http://nhjschulz.github.io/1.0/pargen http://nhjschulz.github.io/xsd/pargen_1.0.xsd" >
                <pd:container name="{Path(self.input_hex_file).stem}_ABMHD" at="0x{self.abmhd_addr:0X}">
                    <pd:blocks>
                        <pd:block offset="0x0000" name="ABMHD" length="0x20" fill="0x00" endianness="LE">
                            <pd:comment>Aurix Alternate Bootmode Header Structure</pd:comment>
                                <pd:data>
                                    <pd:param offset="0x00" name="STADABM" type="uint32">
                                        <pd:comment>User Code Start Address in ABM mode</pd:comment>
                                        <pd:value>0x{self.stad_addr:0X}</pd:value>
                                    </pd:param>
                                    <pd:param offset="0x04" name="ABMHDID" type="uint32">
                                        <pd:comment>Alternate Boot Mode Header Identifier (0xFA7CB359 = OK)</pd:comment>
                                        <pd:value>0x{self.hdr_id:0X}</pd:value>
                                    </pd:param>
            
                                    <pd:param offset="0x08" name="CHKSTART" type="uint32">
                                        <pd:comment>Memory Range to be checked - Start Address</pd:comment>
                                        <pd:value>0x{self.min_addr:0X}</pd:value>
                                    </pd:param>
                                    <pd:param offset="0x0C" name="CHKEND" type="uint32">
                                        <pd:comment>Memory Range to be checked - End Address</pd:comment>
                                        <pd:value>0x{self.max_addr - 0x4:0X}</pd:value>
                                    </pd:param>
            
                                    <pd:param offset="0x010" name="CRCRANGE" type="uint32">
                                        <pd:comment>Check Result for the Memory Range</pd:comment>
                                        <pd:value>0x{self.user_crc:0X}</pd:value>
                                    </pd:param>
                                    <pd:param offset="0x0014" name="CRCRANGE_N" type="uint32">
                                        <pd:comment>Inverted Check Result for the Memory Range</pd:comment>
                                        <pd:value>0x{(~self.user_crc) & 0xffffffff:0X}</pd:value>
                                    </pd:param>
            
                                    <pd:crc offset="0x18" name="CRCABMHD" type="uint32" >
                                        <pd:memory from="0x00" to="0x17" access="32" swap="true"/>
                                        <pd:config polynomial="0x04C11DB7" init="0xFFFFFFFF" rev_in="true" rev_out="true" final_xor="true" ></pd:config>
                                    </pd:crc>
                                    <pd:crc offset="0x1C" name="CRCABMHD_N" type="uint32">
                                        <pd:memory from="0x00" to="0x17" access="32" swap="true"/>
                                        <pd:config polynomial="0x04C11DB7" init="0xFFFFFFFF" rev_in="true" rev_out="true" final_xor="false" ></pd:config>
                                    </pd:crc>
                                </pd:data>
                        </pd:block>
                    </pd:blocks>
                </pd:container>
            </pd:pargen>
            '''
        ).encode()
