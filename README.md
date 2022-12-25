# Pargen - A tool for Flashable Parameter Container Creation

ParGen is an embedded development tool for generation of parameters values that
can be stored in flash memory and maintained independently from the application.
It allows to alter/update parameter values without recompilations.

## Concept and Features

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

To use unreleased development builds or setting up a
development environment for Pargen, please read the
[Developing](https://github.com/nhjschulz/flashcontainer/blob/master/Developing.md/)
page on Github.

## XML Definitions File

The flash container configuration for pargen is provided via an XML
definition file that is explained below.

### TL;DR

The [examples](https://github.com/nhjschulz/flashcontainer/tree/master/examples)
folder shows how to configure Pargen for various flash container
use cases and most of it is likely self explanatory. Refer to the examples.md
files inside the examples folder to learn more about them. To understand Pargen's
XML capabilities in depth, read on.

### XML Configuration File Anatomy

The XML follows an XSD-schema defined n pargen_1.0.xsd. It is highly
recommended to use an XML editor with schema validation support to
avoid or detect validations already while editing. Visual Studio Code would
be a perfect choice, given the "XML Language Support" extension from 
Red Hat is installed. This extensions brings validation and "IntelliSense"
to editing XML files.

The file defines the following data element hierarchy. The "..." lines mean
that the preceding element may appear multiple times:

      <pd:Container ...>
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

    <?xml version="1.0" encoding="utf-8"?>
    <pd:parameterDef xmlns:pd="http://nhjschulz.github.io/1.0/pargen"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://nhjschulz.github.io/1.0/pargen https://nhjschulz.github.io/xsd/pargen_1.0.xsd"">
    

### Container Element
The top level configuration element is the **container**. A container
maps contained blocks to their absolute address by the **at** attribute.
All address specified on block element level are offsets to the
**at** attribute.

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
A block element defines a coherent memory area inside a container. 
A container may have 1 to many block children inside a blocks element.
Blocks hold an optional header and a list of parameters or crc elements.

#### Block Attributes

|Attribute  |Description              |optional|default|
|-----------|-------------------------|--------|-------|
| name      | The block name.         |   No   |       |
| offset    | Memory start offset inside container. Value may be "*" to use the next free offset in container.|No||
| length    | Number of bytes covered by this block|No|
| align     | block alignment to the next 1,2,4,8 bytes boundary|Yes|1|
| fill      | byte value used to fill gaps.|Yes| 0x00 |
| endianness| LE or BE: Little or or big endian byte order |Yes|LE| 

#### Block Child Elements 

|Element  |Description              | Multiplicity |
|---------|-------------------------|--------------|
| comment | Optional comment text for this block| 0..1|
| header  | Optional header with id, version and length information | 0..1  |
| data    | Parent element for block parameter| 1 |

#### Block Header Element

Pargen blocks offers the generation of a header at the beginning of the 
block memory area. This optional header contains block identification,
version and length information. The header supports parameter validation
to verify correctness and compatibility with the using application during
runtime. The safety example in the examples folder shows how to use the 
header in combination with a CRC for this purpose.

The header data is a 16 byte long data structure with the following layout:

    struct sruct_pargen_header_type
    {
        uint16_t id;        /* from id header attribute */
        uint16_t major;     /* from major header attribute */
        uint16_t minor;     /* from minor header attribute */
        uint16_t dataver;   /* from version header attribute */
        uint32_t reserved;  /* reserved = 0x00000000 */
        uint32_t length;    /* from length block attribute */
    };

The header is internally handled as a parameter. That mean the space for any
further parameter starts at offset 16 (0xA) if the header is used.

#### Example Block Element

    <pd:block offset="0x0000" name="UCB_BMHD0" length="0x1F4" fill="0x00" endianness="LE">
        <pd:header id="0x0A" major="1" minor="0" version="1"></pd:header>
        <pd:comment>Aurix Bootmode Headers</pd:comment>
        <pd:data>
          ....
        </pd:data>
    </pd:block>

### Parameter Element

A parameter element defines a single parameter inside a block. 

#### Parameter Element Attributes

|Attribute  |Description              |optional|default|
|-----------|-------------------------|--------|-------|
| offset    | Memory start offset inside block. Value may be "*" to use the next free offset in container.|No||
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
The value element text of a parameter holds the parameter value using
a JSON style syntax. The following  subset of Json literals is supported:

|Value type                        | Examples    |
|----------------------------------|--------------|
| Integer values in decimal or hexadecimal | 1, -2, 0xABCDEF |
| Floating point variables  | 3.141, 1E-005 | 
| Strings in double quotes  | "Hello world!" |
| One-dimensional arrays    | [1, 2, 3, 4, 5, 6] |

### Crc Element

The crc element defines a an integer parameter. The difference to an
integer parameter is the automatic value calculation using a
crc algorithm. Instead of a value child element, a memory
and config element are used to define the crc calculation parameters.

#### Crc Element Attributes

|Attribute  |Description              |optional|default|
|-----------|-------------------------|--------|-------|
| offset    | Memory start offset inside block. Value may be "*" to use the next free offset in container.|No||
| name      | The parameter name.         |   No   |       |
| type      |Parameter type, one of uint{bits} with bits one of 8,16,32,64|No|
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
byte swapping is needed.

Attribute  |Description              |optional|default |
|-----------|-------------------------|--------|-------|
| from    | Start address for crc calculation  |No|    |
| to      | End address for crc calculation    |No|    |
| access  | Bit width in case of swapping (8,16,32,64)|yes|8|
| swap    | Enable bytes swapping using access size|Yes|false|

#### Crc Config Element
The config element defines the crc calculation parameters to 
enable arbitrary crc methods. The values for common used crc methods can be taken from this
[crc catatlog page](https://reveng.sourceforge.io/crc-catalogue/all.htm). The default values select the 
IEEE802.3 calculation also known as CRC-32. Note that the
bit size of the crc is not part of these parameters, but 
derived from the type attribute of the crc element.

Attribute  |Description              |optional|default |
|-----------|-------------------------|--------|-------|
| polynomial| polynomial coefficients   |yes|0x04C11DB7|
| init      | Start value, usual 0 or -1|yes|0xFFFFFFFF|
| rev_in  | Process bytes MSB(false) or LSB(true) first.|yes|true|
| rev_out   | Enable reflection of final crc result|Yes|true|
| final_xor | Perform final XOR of the crc|yes|true|

#### Crc Element Example
    <pd:crc offset="0x008" name="CRCBMHD"type="uint32" >
      <pd:memory from="0x0000" to="0x0007" access="32" swap="true"/>
      <pd:config polynomial="0x04C11DB7" init="0xFFFFFFFF" rev_in="true" rev_out="true" final_xor="true" ></pd:config>
    </pd:crc>
     


## Issues, Ideas And Bugs

If you have further ideas or you found some bugs, great! Create an
[issue](https://github.com/nhjschulz/flashcontainer/issues)
or if you are able and willing to fix it by yourself, clone
the repository and create a pull request.

## License

The whole source code is published under the
[BSD 3-Clause License](https://opensource.org/licenses/BSD-3-Clause/).
Consider also the different licenses of used third party libraries too!

## Contribution

We welcome contribution, but unless you explicitly state otherwise:
Any contribution intentionally submitted for inclusion in the work by you,
shall be licensed as above, without any additional terms or conditions.
