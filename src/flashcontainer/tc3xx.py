""" Flash container generation tailored for TC3XX processors
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

import logging
import sys

from flashcontainer.tc3xx_abmhd import Tc3xxAbmhd
from flashcontainer.packageinfo import __version__, __email__, __repository__
from flashcontainer.fileargparse import FileArgumentParser

# list of tc3xx subcommand classes
_TC3XX_CMDS = [ Tc3xxAbmhd() ]


def tc3xx(argv) -> int:
    """ cmd line interface for tc3xx"""

    logging.basicConfig(encoding='utf-8', level=logging.WARNING)

    name = "tc3xx"
    about = f"{name} {__version__}: Build Pargen definitions for TC3xx data structures."

    parser = FileArgumentParser(
        prog=name,
        description=about,
    )

    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    sub_parsers = parser.add_subparsers(
        title="supported sub commands",
        help='additional command specific help')

    # register all sub commands with the arg parser
    for sub_cmd in _TC3XX_CMDS:
        sub_cmd.register(sub_parsers)

    args = parser.parse_args(argv)

    if 'func' not in vars(args):
        parser.print_help()
        return -1

    return args.func(args)

def tc3xx_cli() -> int:
    """CLI wrapper for tc3xx """

    return tc3xx(sys.argv[1:])

if __name__ == "__main__":
    try:
        sys.exit(tc3xx_cli())
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception(exc)
        sys.exit(-1)
