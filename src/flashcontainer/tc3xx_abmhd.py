""" Alternate boot mode header generation for  TC3XX processors
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
import logging
from enum import Enum
from pathlib import Path

from intelhex import IntelHex

from flashcontainer.tc3xx_cmd import Tc3xxCmdBase
from flashcontainer.pargen import pargen
from flashcontainer.hexwriter import HexWriter
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
        self.output_hex_file = ""

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
            """Generate TC3XX alternate boot mode header for user data\n\n"""
            """Example:\n"""
            """    tc3xx --stad 0x80028000 --from 0x8002000 --to 0x8004000 -o abmhdr 0x80000100 fw.hex""" )

        parser.add_argument(
            "--stad", "-s", nargs=1,
            type=lambda x: int(x,0),
            metavar="STADABM",
            help='User code start address (default: lowest address in input hexfile)'
        )
        parser.add_argument(
            "--from", "-f", nargs=1,
            type=lambda x: int(x,0),
            dest='chk_from',
            metavar="CHKSTART",
            help='Begin of range to be checked (default: lowest address in input hexfile)'
        )
        parser.add_argument(
            "--to", "-t", nargs=1,
            type=lambda x: int(x,0),
            dest='chk_to',
            metavar="CHKEND",
            help='End of range to be checked (default: highest address in input hexfile)'
        )

        parser.add_argument(
            "--abmhdid", "-i", nargs=1,
            type=lambda x: int(x,0),
            metavar="ABMHDID",
            default=0xFA7CB359,
            help=f'Alternate Boot Mode Header Identifier value (default=0x{Tc3xxAbmhd._abmhd_ok_id:X})'
        )

        parser.add_argument(
            "--output", "-o", nargs=1,
            metavar="filename",
            help='Filename of resulting boot mode header hex file (default: <input>_abmhdr.hex)'
        )

        parser.add_argument(
            'address',
            nargs=1,
            metavar='ADDRESS',
            type=lambda x: int(x,0),
            help='Start address of alternate boot mode header.')

        parser.add_argument(
            'filename',
            metavar='HEXFILE',
            nargs=1,
            help='name of hexfile with user code content')

        parser.set_defaults(func=Tc3xxAbmhd._static_run)


    def run(self, args) -> int:
        """Generate alternate boot load header structure hex file."""

        result = RETVAL.OK.value

        print (args)
        result = self._evaluate_arguments(args)

        if RETVAL.OK.value == result:
            result = self.validate()

            if RETVAL.OK.value == result:
                self.calc_user_data_crc()
                result = self.call_pargen()

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
        self.max_addr = args.chk_to[0]if args.chk_to is not None else self.input_hex_data.maxaddr()
        self.stad_addr = args.stad[0] if args.stad is not None else self.min_addr
        self.hdr_id = args.abmhdid if args.abmhdid is not None else Tc3xxAbmhd._abmhd_ok_id

        if args.output is None:
            self.output_hex_file = str(Path(self.input_hex_file).with_suffix("")) + "_abmhd"
        else:
            self.output_hex_file = args.output[0]

        return RETVAL.OK.value

    def validate(self) -> int:
        """Check correctness of received input"""

        # Validate  check address range information
        if (self.min_addr < self.input_hex_data.minaddr()) or (self.min_addr >= self.input_hex_data.maxaddr()):
            logging.error(
                "check start address 0x%08x out of user data range 0x%08x - 0x%08x",
                self.min_addr,
                self.input_hex_data.minaddr(),
                self.input_hex_data.maxaddr()
            )
            return RETVAL.INVALID_PARAMETER.value

        if (self.max_addr < self.input_hex_data.minaddr()) or (self.max_addr > self.input_hex_data.maxaddr()):
            logging.error(
                "check end address 0x%08x out of user data range 0x%08x - 0x%08x",
                self.min_addr,
                self.input_hex_data.minaddr(),
                self.input_hex_data.maxaddr()
            )
            return RETVAL.INVALID_PARAMETER.value

        if self.max_addr < self.min_addr:
            logging.error(
                "invalid check data range 0x%08x - 0x%08x",
                self.min_addr,
                self.max_addr
            )
            return RETVAL.INVALID_PARAMETER.value

        #validate start address
        if (self.stad_addr < self.input_hex_data.minaddr()) or (self.stad_addr >= self.input_hex_data.maxaddr()):
            logging.error(
                "user code start address 0x%08x out of user data range 0x%08x - 0x%08x",
                self.stad_addr,
                self.input_hex_data.minaddr(),
                self.input_hex_data.maxaddr()
            )
            return RETVAL.INVALID_PARAMETER.value

        if 0 != (self.stad_addr & 0x3):
            logging.error(
                "user code start address 0x%08x must be WORD aligned",
                self.stad_addr
            )
            return RETVAL.INVALID_PARAMETER.value

        if 0 != (self.min_addr & 0x3):
            logging.error(
                "check start address 0x%08x must be WORD aligned",
                self.stad_addr
            )
            return RETVAL.INVALID_PARAMETER.value

        if 0 != (self.max_addr & 0x3):
            logging.error(
                "check end address 0x%08x must be WORD aligned",
                self.stad_addr
            )
            return RETVAL.INVALID_PARAMETER.value

        return RETVAL.OK.value

    def calc_user_data_crc(self):
        """Build CRC value over user data."""

        user_data = bytearray()

        for address in range (self.min_addr, self.max_addr):
            user_data.append(self.input_hex_data[address])

        crc_cfg = CrcConfig(
                poly=0x04C11DB7, width=32,
                init=0xFFFFFFFF, revin=True, revout=True, xor=True,
                access=32, swap=True)
        crc_calculator = Crc(crc_cfg)
        self.user_crc = crc_calculator.checksum(crc_calculator.prepare(user_data))


    def call_pargen(self) -> int:
        """Run pargen to produce ABMHDR hex file"""

        # parameter values to patch with cmd arguments in XML
        modifier_dict = {
            "STADABM" : hex(self.stad_addr),
            "ABMHDID" : hex(self.hdr_id),
            "CHKSTART" : hex(self.min_addr),
            "CHKEND" : hex(self.max_addr),
            "CRCRANGE" : hex(self.user_crc),
            "CRCRANGE_N" : hex((~self.user_crc) & 0xFFFFFFFF)
        }

        return pargen(
            cfgfile=Tc3xxAbmhd._abmhd_xml,
            filename=Path(self.output_hex_file).stem,
            outdir=Path(self.output_hex_file).parent,
            static=True,
            writers=[HexWriter],
            modifier=modifier_dict)
