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

__version__ = "0.0.1"

from  xmlparser import XmlParser
import datamodel as DM
import hexwriter
import cfilewriter
import argparse
import logging
import copy

def main() -> int:
    """ Parameter generator tool entry point"""

    logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

    about = 'A tool for generating flashable parameter container.'
    name = "pargen"

    parser = argparse.ArgumentParser(prog = name, description=about)
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--ihex', nargs=1,help="Generate intelhex file with given name.")
    parser.add_argument('--csrc', nargs=1,help="Generate c/c++ header and source file using given basename.")
    parser.add_argument('file',   nargs=1, help='XML parameter definition file')

    args = parser.parse_args()

    print(f"{name} {__version__} : {about}")
    print ("copyright (c) 2022 haju.schulz@online.de\n")


    model = XmlParser.from_file(args.file[0])


    param = {
        "PNAME"   : name,
        "VERSION" : __version__,
        "INPUT"   : args.file[0]
        }

    if (args.ihex is not None):
        try:
            my_params = copy.deepcopy(param)
            my_params.update({"FN" : args.ihex[0]})
            logging.info(f"Generating intelhex file {args.ihex[0]}")
            writer = hexwriter.HexWriter(model, my_params)
            writer.run()
        except Exception as exc:
            logging.exception(exc)

    if (args.csrc is not None):
        try:
            my_params = copy.deepcopy(param)
            my_params.update({"FN" : args.csrc[0]})
            logging.info(f"Generating Cfiles {args.csrc[0]}.[ch]")
            writer = cfilewriter.CFileWriter(model, my_params)
            writer.run()
        except Exception as exc:
            logging.exception(exc)

    return 0

if __name__ == "__main__":
    main()
