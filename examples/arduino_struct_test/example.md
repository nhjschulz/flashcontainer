# Arduino Example with PlatformIO

This example generates a hex file with a parameter block that
gets used as EEPROM content on an ATmega328P processor. It is
executable without hardware using the simavr simulator.
This simulator is part of the
[PlatformIO](https://platformio.org/) toolchain for this processor.
PlatformIO must therefore be installed to run or rebuild the example.

## Running the example with SimAVR

The script [run_simavr.sh](./run_simavr.sh) shows how to run the
example. It provides the following option to SimAVR:

    $HOME/.platformio/packages/tool-simavr/bin/simavr
      -m atmega328p
      -f 16000000L
      -ee param/param.hex
      .pio/build/ATmega328P/firmware.hex

The example will generate the following output:

    ./run_simavr.sh
    AVR: 'param\param.hex' invalid ihex format (; AU)
    Loaded 1 section of ihex
    Load HEX eeprom 81000000, 1024
    Loaded 1 section of ihex
    Load HEX flash 00000000, 3704
    Found pargen block header in EEPROM: ID:EE Version:1.0 Length: 1024     bytes.
    This message is defined as a Pargen parameter!..
    This message is defined as a Pargen parameter!..
    This message is defined as a Pargen parameter!..
    This message is defined as a Pargen parameter!..
    This message is defined as a Pargen parameter!..

The repeated output message and update delay is configured by
parameters from the pargen configuration.
The warning about an invalid ihex format can be ignored. SimAVR reads passed the end
record of the file and complains about the "; ..." comment at the end of the file.

## Noteworthy Configuration

The example deviates from a 'normal' arduino project in the following ways

  1) It contains a pargen configuration for header, hex and link file
     generation.
  2) It uses a modified linker script to generate parameter symbols
  3) It includes the pargen generated header file
  4) It customizes the call to simavr to include the EEPROM data

### Pargen Configuration

The param folder holds the [pargen configuration XML](./param/param.hex).
It creates a parameter block with header ID 0xEE at the logical
address 0x8100000. This address is required by the avr gcc toolchain
as the start of the EEPROM space. The following pargen options are
needed to regenerate the required project files:

    pargen --ihex --gld --csrc -o param param/param.xml

The display message and repeat delay can be changed inside the XML
before rerunning pargen. The example will use the changed values
in the next simavr run without the need for recompiling.

### Modified Linker Script

The example needs a local copy of the avr linker script avr5.xn.
This is required to add the include directive for the pargen linker
script into it. Add the following configuration option to the
platformio.ini file to use the local copy:

    [env:ATmega328P]
    ...
    board_build.ldscript = avr5.xn

Note: To find out the path to the original linker script, add the
following option to the "env:ATmega328P" section as well:

    build_flags = -Wl,--verbose

The modification is the following single line addition into the eeprom
section definition:

        INCLUDE param/param.ld  /* Add pargen generated symbols */

The eeprom section will then look like this:

    .eeprom  :
      {
        INCLUDE param/param.ld  /* Add pargen generated symbols */
        /* See .data above...  */
        KEEP(*(.eeprom*))
         __eeprom_end = . ;
      }  > eeprom

The include file will generate public symbols for all pargen
parameters at their EEPROM addresses.

### Using the Include File to Access Parameters

The file [src/main.cpp](./src/main.cpp) includes the
param/param.h header file to access the parameters from the
application code. The generated C-Source file is not used by the
application. It is intended for test development purposes only.

### Providing the EEPROM data to SimAVR

The EEPROM data from pargen is passed to SimAVR as an additional
hexfile together with the application. The file param/param.hex
is passed together with the "-ee" option to tell the simulator
that this is EEPROM data.

    simavr ... -ee param/param.hex  ...
