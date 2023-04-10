# Tools for Creating Flashable Parameter Container

![License](https://img.shields.io/badge/License-BSD%203--Clause-green)
[![Python package](https://github.com/nhjschulz/flashcontainer/actions/workflows/push.yaml/badge.svg?branch=master)](https://github.com/nhjschulz/flashcontainer/actions/workflows/push.yaml)

## Pargen - Parameter File Generator

The main tool in flashcontainer is called Pargen. Pargen is generating data files
for parameter values or other data structures that can to be stored in flash memory.
It allows to change the data without recompilation by reading definitions from an
XML file.

Flashcontainter also includes tailored front ends for Pargen to simplify special
use cases. See the [TC3xx tool](#generating-tc3xx-boot-mode-header-structures)
description chapter for generating Infineon Aurix TC3xx boot mode headers structures.

## Concept and Features

![Concept](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/nhjschulz/flashcontainer/master/overview.plantuml)

* Read input from a schema validated XML file
* Generate C-Source stubs for embedding into the application source amd testing environments
* Generate Intel Hex files for flashing with a programmer
* Generate GNU linker include file for mapping the parameter to absolute addresses

## Installation

The package is available on Pypi and can be installed using

    pip install flashcontainer

A python 3.8 or higher version is required.

The parameter generator tool can then by called on cmdline using

    $ pargen -h
    usage: pargen [-h] [--ihex] [--csrc] [--gld] [--a2l] [--pyhexdump] [--destdir directory] [--filename basename] [--static] [--modify name=value] [--version] file
    
    pargen 0.4.0: A tool for generating flashable parameter container.
    
    positional arguments:
      file                  name of the XML parameter definition file
    
    optional arguments:
      -h, --help            show this help message and exit
      --ihex                generate intelhex file
      --csrc                generate c/c++ header and source files
      --gld                 generate GNU linker include file for parameter symbol generation
      --a2l                 generate A2L parameter description file
      --pyhexdump           generate pyHexDump print configuration file
      --destdir directory, -o directory
                            specify output directory for generated files
      --filename basename, -f basename
                            set basename for generated files
      --static, -s          create static comment output without dynamic elements like date and time
      --modify name=value, -m name=value
                            modify parameter value using name=value notation
      --version             show program's version number and exit
    
    Copyright (c) 2022-2023 Haju Schulz <haju.schulz@online.de>. Visit https://github.com/nhjschulz/flashcontainer for full documentation and examples.

 The flashcontainer 
[Developing](https://github.com/nhjschulz/flashcontainer/blob/master/Developing.md/)
page on Github explains how to use unreleased development builds
or how to setup a development environment.

## XML Definitions File

The flash container configuration for Pargen is a XML
definition file with the format explained below.

### TL;DR

The [examples](https://github.com/nhjschulz/flashcontainer/tree/master/examples)
folder shows how to configure Pargen for various use cases.
Most of it is likely self explanatory. Read the examples.md
files inside the examples folder to learn more about them. To
understand Pargen's XML capabilities in depth, read on.

### XML Configuration File Anatomy

The XML follows an XSD-schema defined in 
[pargen_1.0.xsd](https://github.com/nhjschulz/flashcontainer/blob/master/src/flashcontainer/pargen_1.0.xsd).
It is highly recommended to use an XML editor with schema validation
support to avoid or detect validations already while editing.
Visual Studio Code is a perfect choice, given the 
"XML Language Support" extension from Red Hat is installed.
This extensions brings validation and "IntelliSense" to editing XML files.

The file defines the following data element hierarchy. The "..." lines mean
that the preceding element may appear multiple times:

      <pd:Container>
        <pd:blocks>
          <pd:block>
            <pd:parameter> or <pd:crc>
            ...
          </pd:block>
          ...
        <pd:blocks>
        ...
      </pd:Container>

### XML Root Element

The XML file uses XSD schema validation and a namespace. This requires the
following (static) XML element to be used as the root XML element at the
beginning of the file:

    ?xml version="1.0" encoding="utf-8"?>
    <pd:pargen xmlns:pd="http://nhjschulz.github.io/1.0/pargen"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://nhjschulz.github.io/1.0/pargen http://nhjschulz.github.io/xsd/pargen_1.0.xsd" >

### Container Element

The top level configuration element is the **container**. A container
maps its parameter blocks to absolute addresses by the **at** attribute. Address attributes inside block elements are offsets to the
**at** attribute value.

#### Container Element Attributes

|Attribute  |Description              |optional|default|
|-----------|-------------------------|--------|-------|
| name      | The container name.     |   No   |       |
| at        | Absolute address of the container.|No||

#### Container Child Elements

|Element  |Description              | Multiplicity |
|---------|-------------------------|--------------|
| blocks  | Parent Element for blocks|  1          |

#### Example Container Element

    <pd:container name="UCBRange" at="0xAF400000">
      <pd:blocks>
      ....
      </pd:blocks>
    </pd:container>

### Block Element

A block element defines a contiguous memory area inside a container.
Blocks contain an optional header and parameters at unique offsets
inside the block memory range. Gaps between parameters are filled
with the byte value specified using the 'fill' attribute.
A container may have 1 to many block children inside a blocks element.

#### Block Attributes

|Attribute  |Description              |optional|default|
|-----------|-------------------------|--------|-------|
| name      | The block name.         |   No   |       |
| offset    | Memory start offset inside container. Value may be "." to use the next free offset inside the container.|No||
| length    | Number of bytes covered by this block|No|
| align     | block alignment to the next 1,2,4,8 bytes boundary|Yes|1|
| fill      | byte value used to fill gaps.|Yes| 0x00 |
| endianness| LE or BE: Little or big endian byte order |Yes|LE|

#### Block Child Elements

|Element  |Description              | Multiplicity |
|---------|-------------------------|--------------|
| comment | Optional comment text for this block| 0..1|
| header  | Optional header with id, version and length information | 0..1  |
| data    | Parent element for block parameter| 1 |

#### Block Header Element

Pargen blocks may contain a header at the beginning of the
block memory area. This optional header contains block identification,
version and length information. The header supports parameter validation
to verify correctness and compatibility with the using application during
runtime. The 
[safety example](https://github.com/nhjschulz/flashcontainer/tree/master/examples/safety/)
in the examples folder shows how to use the header in combination with a
CRC for this purpose.

The header data is a 16 byte long data structure with the following
layout:

    struct sruct_pargen_header_type
    {
        uint16_t id;        /* from id header attribute */
        uint16_t major;     /* from major header attribute */
        uint16_t minor;     /* from minor header attribute */
        uint16_t dataver;   /* from version header attribute */
        uint32_t reserved;  /* reserved = 0x00000000 */
        uint32_t length;    /* from length block attribute */
    };

Application can freely decide how to use the id, major, minor and dataver
header fields. The proposed usage is as follows:

* id - A unique id to identify the blocks purpose. (Example: 1:CAN Bus settings, 2 :Motor parameters, ...)
* Major.Minor - A version pair defining the layout of the block
* dataver - The version or build number of the parameter set

The header data is internally handled as a parameter. Space for any
further parameter starts at offset 16 (0x10) if the header is used.

#### Example Block Element

    <pd:block offset="0x0000" name="UCB_BMHD0" length="0x1F4" fill="0x00" endianness="LE">
        <pd:header id="0x0A" major="1" minor="0" version="1"></pd:header>
        <pd:comment>Aurix Bootmode Headers</pd:comment>
        <pd:data>
          ....
        </pd:data>
    </pd:block>

### Parameter Element

A parameter element defines a single parameter inside a block. Blocks may
have one to many parameter elements.

#### Parameter Element Attributes

|Attribute  |Description              |optional|default|
|-----------|-------------------------|--------|-------|
| offset    | Memory start offset inside block. Value may be "." to use the next free offset inside the block.|No||
| name      | The parameter name.         |   No   |       |
| type      |Parameter type, one of [u]int{bits} with bits one of 8,16,32,64 or float32,float64 or utf8|No|
| align     | Parameter offset alignment to the next 1,2,4,8 bytes boundary|Yes|1|


#### Parameter Child Elements

|Element  |Description              | Multiplicity |
|---------|-------------------------|--------------|
| comment | Optional comment text for this parameter| 0..1|
| value   | The parameter value     | 1  |

#### Parameter Element Example

    <pd:param offset="0x004" name="STAD" type="uint32">
      <pd:comment>Application entry point address</pd:comment>
      <pd:value>0x80028000</pd:value>

#### Parameter Value Element

The value element of a parameter holds the parameter value inside
its text element using a JSON style syntax. The following subset of
JSON definitions are supported:

|Value type                        | Examples    |
|----------------------------------|--------------|
| Integer values in decimal or hexadecimal | 1, -2, 0xABCDEF |
| Floating point variables  | 3.141, 1E-005 |
| Strings in double quotes  | "Hello world!" |
| One-dimensional arrays    | [1, 2, 3, 4, 5, 6] |

### Crc Element

The crc element defines an integer parameter. The difference to a
normal integer parameter is the automatic value calculation using a
crc algorithm. Instead of a parameter value child element, memory
and config elements are used to define crc calculation parameters.

#### Crc Element Attributes

|Attribute  |Description              |optional|default|
|-----------|-------------------------|--------|-------|
| offset    | Memory start offset inside block. Value may be "." to use the next free offset inside the block|No||
| name      | The crc parameter name.   |   No   |       |
| type      | Parameter type, one of uint{bits} with bits one of 8,16,32,64|No|
| align     | Parameter offset alignment to the next 1,2,4,8 bytes boundary|Yes|1|

#### Crc Child Elements

|Element  |Description              | Multiplicity |
|---------|-------------------------|--------------|
| comment | Optional comment text for this parameter| 0..1|
| memory   | The crc memory range and access method| 1  |
| config   | The optional crc computation parameter| 0..1|

#### Crc Memory Element

The memory element defines the memory range used to calculate
the crc and the access method to this memory range if
byte swapping is needed. The bytes at the range boundaries are
included into the crc calculation.

Attribute  |Description              |optional|default |
|-----------|-------------------------|--------|-------|
| from    | Start address for crc calculation  |No|    |
| to      | End address for crc calculation. The value may be "." to represent an address right before the crc offset.|No|    |
| access  | Bit width in case of swapping (8,16,32,64)|yes|8|
| swap    | Enable bytes swapping using access size|Yes|false|

#### Crc Config Element

The config element defines the crc calculation parameters to
enable arbitrary crc methods. The values for common used crc methods
can be taken from this
[crc catalog page](https://reveng.sourceforge.io/crc-catalogue/all.htm).
The default values select the IEEE802.3 crc calculation also known as
CRC-32. Note that the bit size of the crc is not part of these parameters,
but derived from the type attribute of the crc element.

|Attribute  |Description              |optional|default |
|-----------|-------------------------|--------|-------|
| polynomial| polynomial coefficients   |yes|0x04C11DB7|
| init      | Start value, usual 0 or -1|yes|0xFFFFFFFF|
| rev_in  | Process bytes MSB(false) or LSB(true) first.|yes|true|
| rev_out   | Enable reflection of final crc result|Yes|true|
| final_xor | Perform final XOR of the crc|yes|true|

#### Crc Element Example

    <pd:crc offset="0x008" name="CRCBMHD" type="uint32">
      <pd:memory from="0x0000" to="0x0007" access="32" swap="true"/>
      <pd:config polynomial="0x04C11DB7" init="0xFFFFFFFF" rev_in="true" rev_out="true" final_xor="true" ></pd:config>
    </pd:crc>


## Generating TC3xx Boot Mode Header Structures

The tc3xx tool is used to generate Pargen definition XML files for boot mode header
structures. A Boot mode header structure is a data block in flash memory, which is
defined by Infineon TC3xx processors. It gets processed by startup software to 
select which image to boot into.

General usage of the tc3xx command:

    tc3xx  [-h] [--version] {tool name} ...


### TC3xx ABMHD - Alternate Boot Mode Header Generator

Tc3xx supports the *abmhd* tool to a generate an alternate boot mode header structure for firmware hex files. 
The *tc3xx abmhd* tool is controlled by options and produces a Pargen definition file. The definitions file is 
written to stdout id no output file option is given. This allows to "pipe" the definitions directly into Pargen.

*tc3xx abmhd* usage:

    usage: tc3xx abmhd [-h] [--stad STADABM] [--from CHKSTART] [--to CHKEND] [--abmhdid ABMHDID] [--output filename] ADDRESS HEXFILE    

    Generate TC3XX alternate boot mode header Pargen definition file.   

    Example:
        tc3xx abmhd --stad 0x80028000 --from 0x8002000 --to 0x8004000  0x80000100 fw.hex | pargen --ihex -f abmhd -   

    positional arguments:
      ADDRESS               flash address of alternate boot mode header.
      HEXFILE               name of hexfile with user data content    

    options:
      -h, --help            show this help message and exit
      --stad STADABM, -s STADABM
                            user code start address (default: lowest address in hexfile)
      --from CHKSTART, -f CHKSTART
                            begin of range to be checked (default: lowest address in hexfile)
      --to CHKEND, -t CHKEND
                            end of range to be checked (default: highest address in hexfile + 1)
      --abmhdid ABMHDID, -i ABMHDID
                            alternate Boot Mode Header Identifier value (default=0xFA7CB359)
      --output filename, -o filename
                            file name of generated Pargen xml file (default: <stdout>)

## Issues, Ideas And Bugs

If you have further ideas or you found some bugs, great! Create an
[issue](https://github.com/nhjschulz/flashcontainer/issues)
or if you are able and willing to fix it by yourself, clone
the repository and create a pull request.

## Used Non Standard Python Libraries

The project uses the following non standard python libraries:
|Library  |Purpose |License |                   
|---------|--------|--------|
|[lxml](https://pypi.org/project/lxml/)| XML parsing and validation|BSD-3-Clause|
|[intelhex](https://pypi.org/project/intelhex/)|intel hex file generation|BSD|
|[json5](https://pypi.org/project/json5/)|JSON read and write (with hexadecimal number support)|Apache|
|[toml](https://pypi.org/project/toml/)|Accessing toml file content|MIT|

## License

The whole source code is published under the
[BSD 3-Clause License](https://opensource.org/licenses/BSD-3-Clause/).
Consider also the different licenses of used third party libraries too!

## Contribution

We welcome contribution, but unless you explicitly state otherwise:
Any contribution intentionally submitted for inclusion in the work by you,
shall be licensed as above, without any additional terms or conditions.
