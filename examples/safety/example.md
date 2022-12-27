# Safety Relevant Parameter Block Example

This example generates a hex file with a parameter block that demonstrates
safety measures for parameter handling. The safety measures are

* A Block identification to ensure the expected data is present in memory
* Block versioning to ensure compatibility with the using application
* A checksum to detect data corruption of the block

## Running the example

The recommended options for this example are

    pargen --ihex --gld --csrc --pyhexdump -o gen safety.xml

This creates the hex file, linker include files, a pyHexDump configuration and
C-Language code inside the 'gen' folder.

* The hex file is used for programming the parameter data into device memory.
* The linker include file is used for generating public symbols for the
  parameters at their defined addresses.
* The C-Language header file is used to provide parameter access to the
  application.
* The C-Language source file can be used to access the parameter values in
  test environments like unit-tests or integration tests.
* The pyHexDump configuration can be used to dump the hex file data using the
  pyHexDump tool for verification purposes.

## Noteworthy Configuration

The safety measures mentioned above are implemented using the following
block elements from the safety.xml configuration:

* A header holding id and version information at the beginning of the block.
* A 32-bit CRC at the end of the block that is computed over the entire block
  memory (excluding the CRC bytes)

The header is created using the following XML element:

     <pd:header id="0xFF01" major="1" minor="0" version="3"/>

The crc is added at the end of the block using this element:

    <pd:crc offset="0x1fc" name="crc" type="uint32">
        <pd:comment>Entire block crc32 (IEEE802.3)</pd:comment>
        <pd:memory from="0x0000" to="."/>

This shows a minimal crc definition using the default CRC-32 computation
defined by IEEE802.3. The crc is placed 4 bytes before the end of the
0x200 bytes long block. It covers the entire block space. The "." value
in the 'to' attribute translates to the address right before the Crc
parameter. The default values for calculation are:

    polynomial:0x4C11DB7, 32 Bit, init:0xFFFFFFFF, reverse in:True, reverse out:True, final xor:True, access:1, swap:False

## Running pyHexDump for Validation

The resulting hex file can be printed/validated using
[pyHexDump](https://github.com/BlueAndi/pyHexDump), a highly
configurable binary data dumper. The tool reads the hex file data
and formats the contained parameter data using the pyhexdump configuration
file from pargen:

    $ pyHexdump print -oih .\gen\safety.hex .\gen\safety.pyhexdump
    paraBlkSafety_blkhdr.id @ 80000000: 0xFF01
    paraBlkSafety_blkhdr.major @ 80000002: 0x0001
    paraBlkSafety_blkhdr.minor @ 80000004: 0x0000
    paraBlkSafety_blkhdr.dataver @ 80000006: 0x0003
    paraBlkSafety_blkhdr.reserved @ 80000008: 0x00000000
    paraBlkSafety_blkhdr.length @ 8000000C: 0x00000200
    paraBlkSafety_calibration @ 80000010: [0x3F800000, 0xC0066666, 0x404CCCCD, 0x40900000, 0x40ACCCCD, 0x40D00000]
    paraBlkSafety_crc @ 800001FC: 0x2BB9ACB8

The block crc shown in the end of the above hex output can be checked using
the checksum command from pyHexDump. Note that unlike pargen's crc
configuration, the end address is not included and must therefore
be incremented by one.

    $ pyHexdump checksum -sa 0x80000000 -ea 0x800001FC -s 0xFFFFFFFF -p 0x4C11DB7 -ri -ro -fx  .\gen\safety.hex
    2BB9ACB8