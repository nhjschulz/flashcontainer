# ParGen - A tool for Flashable Parameter Container Creation

ParGen is an embedded development tool for generation of parameters values that
can be stored in flash memory and maintained independent from the application.
It allows to alter/update parameter values without recompilations.

## Concept and Planned Features

![Concept](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/nhjschulz/flashcontainer/master/overview.plantuml)

* Read input from a schema validated XML file
* Generate C-Source stubs for embedding into the application source amd testing environments
* Generate Intel Hex files for flashing with a programmer
* Generate GNU linker include file for mapping the parameter to absolute addresses
* Generate A2L fragments for accessing the parameters from AUTOSAR test environments

## Installation

The package is available on Pypi and can be installed using

    pip install flashcontainer

A python 3.8 or higher version is required.

The parameter generator tool can then by called on cmdline using

    $ pargen -h
    A tool for generating flashable parameter container.

    positional arguments:
      file                  XML parameter definition file

    optional arguments:
      -h, --help            show this help message and exit
      --ihex                Generate intelhex file
      --csrc                Generate c/c++ header and source files
      --gld                 Generate GNU linker include file for parameter symbol generation.
      --dump                Generate pyHexDump print configuration file.
      --destdir DESTDIR, -o DESTDIR
                            Specify output directory for generated files
      --filename FILENAME, -f FILENAME
                            Set basename for generated files.

## Example Usage

TODO

## Issues, Ideas And Bugs

If you have further ideas or you found some bugs, great! Create an [issue](https://github.com/issues) or if you are able and willing to fix it by yourself, clone the repository and create a pull request.

## License

The whole source code is published under the [BSD 3-Clause License](https://opensource.org/licenses/BSD-3-Clause/).
Consider also the different licenses of used third party libraries too!

## Contribution

We welcome contribution, but unless you explicitly state otherwise: Any contribution intentionally submitted for inclusion in the work by you, shall be licensed as above, without any additional terms or conditions.
