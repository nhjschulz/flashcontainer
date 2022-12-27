# Aurix TC3XX Boot Mode Header Generation

This example generates a hex file with Aurix TC3xx boot mode header UCB data.
For details of this data structure.

## Running the example

The recommended options for this example are

    pargen --ihex --pyhexdump -o gen bmhdr.xml

This creates both the hex file, and a configuration for the pyHexdump tool
inside the gen folder. The C-Source or linker data output options are not
needed as the data is processed by internal startup software of the
Aurix processor boot ROM.

## Noteworthy Configuration

The tricky bit for boot mode headers are their checksums. The 8 byte area
from offset 0x0000-0x0007 is verified with a CRC32 checksum, that itself
is repeated bit reversed. The 8 bytes of data used for the checksums
are not read sequentially, but interpreted as two 32-Bit words in
big-endian format. Thats why the configuration XML for the CRC's contain
an access and swap attribute inside the memory element:

    <pd:memory from="0x0000" to="0x007" access="32" swap="true"/>

This line instructs the CRC calculator to read the data as a sequence
of 32-Bit values and byte swap each of them before processing.

## Displaying the Boot Mode Header Data with pyHexDump

The resulting hex file can be printed/validated using
[pyHexDump](https://github.com/BlueAndi/pyHexDump), a highly
configurable binary data dumper. The template file bmhdr.mao
uses the generated hex file and pyhexdump configuration to
pretty print and verify the hex data into markdown format.

    $ pyHexDump print  -tf ./bmhdr.mao ./gen/bmhdr.hex ./gen/bmhdr.pyhexdump

    # Aurix TC397 - Blinky Example

    ## User Control Block 00

    |Short Name|Value|
    |----------|-----|
    | BMI_BMHDID | 0xB359013E |
    | STAD | 0x80028000 |
    | CRCBMHD | 0x8B058D15 |
    | CRCBMHD_N | 0x74FA72EA |
    | PWx | [0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000] |
    | CONFIRMATION | 0x43211234 |

    ### Boot Mode Index (BMI)
    * Mode selection by configuration pins: enabled
    * Start-up mode: internal start from flash

    ### Boot Mode Header Identifier (BMHDID)
    Is boot mode header valid: OK

    ### Boot Mode Header CRC (CRCBMHD/CRCBMHD_N)
    Is boot mode header integrity given: OK

A markdown rendering viewer will show this output as follows:

# Aurix TC397 - Blinky Example

## User Control Block 00

|Short Name|Value|
|----------|-----|
| BMI_BMHDID | 0xB359013E |
| STAD | 0x80028000 |
| CRCBMHD | 0x8B058D15 |
| CRCBMHD_N | 0x74FA72EA |
| PWx | [0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000] |
| CONFIRMATION | 0x43211234 |

### Boot Mode Index (BMI)
* Mode selection by configuration pins: enabled
* Start-up mode: internal start from flash

### Boot Mode Header Identifier (BMHDID)
Is boot mode header valid: OK

### Boot Mode Header CRC (CRCBMHD/CRCBMHD_N)
Is boot mode header integrity given: OK
