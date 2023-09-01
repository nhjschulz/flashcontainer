#!/bin/sh
cmd=$HOME/.platformio/packages/tool-simavr/bin/simavr
$cmd -m atmega328p -f 16000000L -ee param/param.hex .pio/build/ATmega328P/firmware.hex
