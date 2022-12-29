@SET SIM=%USERPROFILE%\.platformio\packages\tool-simavr\bin\simavr
%SIM% -m atmega328p -f 16000000L -ee param\param.hex .pio\build\ATmega328P\firmware.hex
