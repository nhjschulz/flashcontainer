# Development Information

This page explains how to setup a development environment for the
flashcontainer project. The IDE used for developing flashcontainer
is Visual Studio Code. It is not mandatory to use this IDE, but the
following chapters assume the steps are executed from within it.

It is expected that the necessary plug-ins for python development
are already installed into Visual Studio Code.

The project requires Python 3.8 or later.

## Loading the Project into Visual Studio Code

The project is loaded into the IDE by opening the git repository folder
of a cloned sandbox using 'File -> Open Folder' pull-down menu.

## Setup a Virtual Python Environment

Open or switch to a terminal windows inside the IDE. The shell of the
terminal must be at the cloned git repository base folder.

 Run the following command to create a local virtual python environment:

    python -m venv .venv

A popup should appear on the lower right asking for the following:

    "We noticed a new environment has been created. Do you want to select it for the workspace folder?

Answer this question with "Yes" to instruct the IDE to use this virtual environment.

Activate the virtual environment using the following command:

    Windows cmd:         .venv\Scripts\activate.bat
    Windows Power Shell: .venv\Scripts\activate.ps1
    Linux/Macos:          source .venv/bin/activate

Ensure that the virtual environment is used by going to the Command Palette and search for

    Python: Select Interpreter

Choose the one in the .venv folder

## Create a Development Editable Install

An editable install is needed for running the unit tests and development of the package itself.
The following commands installs the project dependencies and the project  as an editable install
into the virtual environment:

    python -m pip install -r requirements.txt
    python -m pip install -e .

The parameter generator tool can then by called on command line in several ways

    $ pargen -h
    $ python -m flashcontainer -h
    $ python src/flashcontainer/pargen.py -h

All above calls would show the tool help text:

    usage: pargen [-h] [--ihex] [--csrc] [--gld] [--pyhexdump] [--destdir DESTDIR] [--filename FILENAME] file

    A tool for generating flashable parameter container.

    positional arguments:
    file                  XML parameter definition file

    optional arguments:
      -h, --help            show this help message and exit
      --ihex                Generate intelhex file
      --csrc                Generate c/c++ header and source files
      --gld                 Generate GNU linker include file for parameter symbol generation.
      --pyhexdump           Generate pyHexDump print configuration file.
      --destdir DESTDIR, -o DESTDIR
                            Specify output directory for generated files
      --filename FILENAME, -f FILENAME
                            Set basename for generated files.

Note: The executable pargen may not be found and pip should have complained about a missing
path. In this case you need to run the script either by the shown full path or add the shown
folder to the PATH environment.

## Build an Installation Package

An installable wheel file can be created using the build package and the following commands:

    python -m pip install --upgrade build
    python -m build

The wheel file will be generated in the dist folder:

    ls dist
    flashcontainer-<version>-py3-none-any.whl   flashcontainer-<version>.tar.gz

## Running the Unit tests

The unit test rely on pytest, so pytest needs to be installed.

    pip install pytest

The test can be run either from the IDE's Testing view or from the console with:

    $ pytest -v
    ================================================= test session starts =================================================
    platform win32 -- Python 3.9.13, pytest-7.2.0, pluggy-1.0.0 -- C:\sb\privat\flashcontainer\.venv\Scripts\python.exe
    cachedir: .pytest_cache
    rootdir: c:\sb\privat\flashcontainer, configfile: pyproject.toml
    collected 11 items

    tests/test_byteconv.py::test_convert_valstr_to_byte PASSED                                                       [  9%]
    tests/test_byteconv.py::test_bytes_to_c_init PASSED                                                              [ 18%]
    tests/test_checksum.py::test_swap PASSED                                                                         [ 27%]
    tests/test_datamodel.py::test_parameter_as_gap PASSED                                                            [ 36%]
    tests/test_datamodel.py::test_header_bytes PASSED                                                                [ 45%]
    tests/test_datamodel.py::test_block_crc PASSED                                                                   [ 54%]
    tests/test_datamodel.py::test_get_bytes_empty PASSED                                                             [ 63%]
    tests/test_datamodel.py::test_get_bytes PASSED                                                                   [ 72%]
    tests/test_datamodel.py::test_get_bytes_with_gaps PASSED                                                         [ 81%]
    tests/test_xmlparser.py::test_parse_int PASSED                                                                   [ 90%]
    tests/test_xmlparser.py::test_calc_addr PASSED                                                                   [100%]

    ================================================= 11 passed in 0.14s ==================================================

## Issues, Ideas And Bugs

If you have further ideas or you found some bugs, great! Create an [issue](https://github.com/issues) or if you are able and willing to fix it by yourself, clone the repository and create a pull request.

## License

The whole source code is published under the [BSD 3-Clause License](https://opensource.org/licenses/BSD-3-Clause/).
Consider also the different licenses of used third party libraries too!

## Contribution

We welcome contribution, but unless you explicitly state otherwise: Any contribution intentionally submitted for inclusion in the work by you, shall be licensed as above, without any additional terms or conditions.
