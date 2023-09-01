#include <Arduino.h>
#include <avr/eeprom.h>

#include "../param/param.h"


/** Crc32 simple implementation without lookup table*/
class Crc32
{
    public:
    Crc32() : m_crc(0xFFFFFFFFUL)
    {
    }

    uint32_t get()
    {
        return ~m_crc;
    }

    void update(uint8_t byte)
    {
        for (uint8_t i = 0; i < 8; ++i)
        {
            uint32_t tmp((byte ^ m_crc) & 0x1u);
            m_crc >>= 1;
            if (0 != tmp) {
                m_crc ^= 0xEDB88320;
            }
            byte >>= 1;
        }
    }

    private:
    uint32_t m_crc;
};

/** Check for expected block in EEPROM and validate content
 *
 * Halts on errors
 */
void setup()
{
    pargen_header_type_t parHdr;

    Serial.begin(9600);
    
    eeprom_read_block(&parHdr, (const void *)&paraBlkSafety_blkhdr, sizeof(parHdr));

    Serial.printf(
        "Found pargen block header in EEPROM: ID:%0X Version:%d.%d Length: %lu bytes\n",
        parHdr.id,
        parHdr.major,
        parHdr.minor,
        parHdr.length
    );
    Serial.printf("Address for safety block header in mem is %p \n", (void *)&paraBlkSafety_blkhdr);
    Serial.println("-------------------------------------------------");

    Serial.println("Testing value out of safety block");
    uint16_t valtest = eeprom_read_word((const uint16_t*)&val);
    Serial.printf("The val in eeprom is %u\n", (unsigned int)valtest);
    Serial.printf("Address for val in mem is %p \n", (void *)&val);
    Serial.println("-------------------------------------------------");

    // output structure content
    uint8_t one = eeprom_read_byte((const uint8_t*)(&simpy.int1));
    uint8_t two = eeprom_read_byte((const uint8_t*)(&simpy.int2));
    uint8_t three = eeprom_read_byte((const uint8_t*)&simpy.smallcrc);

    Serial.println("When reading single values out of structs:");
    Serial.printf("The simple struct contains %d, %d and %d\n", one, two, three);

    pargen_SimpleS_type_t newsimpy;
    eeprom_read_block(&newsimpy, (const void *)&simpy, sizeof(newsimpy));

    Serial.println("When reading the whole struct from eeprom:");
    Serial.printf(
        "Simpy in EEPROM: int1:%d int2:%d smallcrc:%d\n",
        newsimpy.int1,
        newsimpy.int2,
        newsimpy.smallcrc
    );

    Serial.println("-------------------------------------------------");
    Serial.printf("Address for simpy in mem is %p \n", (void *)&simpy);
    Serial.printf("Address for simpy.smallcrc in mem is %p \n", (void *)&simpy.smallcrc);

    /*
    Serial.println("Simpy from param.c holds:");
    Serial.printf(
        "Simpy defined: int1:%d int2:%d smallcrc:%d\n",
        simpy.int1,
        simpy.int2,
        simpy.smallcrc
    );
    */
    
    Serial.println("-------------------------------------------------");
    Serial.printf("Address for biggy in mem is %p \n", (void *)&biggy);
    Serial.printf("Address for biggy.int1 in mem is %p \n", (void *)&biggy.int1);
    Serial.printf("Address for biggy.padding0 in mem is %p \n", (void *)&biggy.padding0);
    Serial.printf("Address for biggy.int2 in mem is %p \n", (void *)&biggy.int2);
    Serial.printf("Address for biggy.padding1 in mem is %p \n", (void *)&biggy.padding1);
    Serial.printf("Address for biggy.intarray in mem is %p \n", (void *)&biggy.intarray);

    pargen_ComplexS_type_t newbiggy;
    eeprom_read_block(&newbiggy, (const void *)&biggy, sizeof(newbiggy));


    Serial.printf("biggy.int1 from EEPROM: %u \n", newbiggy.int1);
    Serial.printf("biggy.int2 from EEPROM: %u \n", newbiggy.int2);
    for(unsigned int i = 0; i < (sizeof(newbiggy.intarray) / sizeof(newbiggy.intarray[0])); i++) 
    {
        Serial.printf("%u, ", newbiggy.intarray[i]);
    }
    Serial.println("\n");

}


void loop()
{
    delay(5000);
}