#include <Arduino.h>
#include <avr/eeprom.h>

#include "../param/param.h"

void setup() 
{
    pargen_header_type_t parHdr;

    Serial.begin(9600);


    eeprom_read_block(&parHdr, (const void *)&par_blkhdr, sizeof(parHdr));

    if (0xee == parHdr.id)
    {
        Serial.printf(
            "Found pargen block header in EEPROM: ID:%0X Version:%d.%d Length: %d bytes\n",
            parHdr.id,
            parHdr.major,
            parHdr.minor,
            parHdr.length
        );
    }
    else
    {
        Serial.println("Fatal: Pargen block header with id 0xEE not present in EEPROM.");
        for(;;)
            ;
    }

    uint16_t delay_ms = eeprom_read_word((const uint16_t*)(&par_UpdateDelay_ms));

    Serial.print( "delay: ");
    Serial.print( delay_ms);
    Serial.print( " @ ");
    Serial.println((int16_t)(&par_UpdateDelay_ms));

}

void loop()
{

    uint16_t delay_ms = eeprom_read_word((const uint16_t*)(&par_UpdateDelay_ms));
    const uint8_t * addr = (const uint8_t *)par_WelcomeMsg_str;
    uint8_t c;

    while(0 != (c = eeprom_read_byte(addr++)))
    {
        Serial.print((char)c);
    }

    delay(delay_ms);
}