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

static void halt()
{
    for(;;)
    {
        ;
    }
}

/** Check for expected block in EEPROM and validate content
 *
 * Halts on errors
 */
void setup()
{
    pargen_header_type_t parHdr;

    Serial.begin(9600);

    /* Recalculate block crc over all block bytes, excluding CRC at the end
     * and compare it with the crc parammeter value at the block end.
     */
    Crc32 crc;
    const uint8_t * eepromAddr = (const uint8_t *)&par_blkhdr;
    eeprom_read_block(&parHdr, (const void *)&par_blkhdr, sizeof(parHdr));

    for (uint16_t count = (parHdr.length-4); count != 0; --count)
    {
        crc.update(eeprom_read_byte(eepromAddr++));
    }

    uint32_t expected_crc = eeprom_read_dword((const uint32_t *)&par_crc);
    if (expected_crc != crc.get())
    {
         Serial.printf(
            "Fatal: CRC error in EEPROM, expected: %08lX, calculated %08lX\n",
            expected_crc,
            crc.get()
         );
         halt();
    }
    else
    {
        Serial.println("EEPROM block CRC check passed.");
    }

    /* A uncorrupted block is present, check its content for expected id
     * and compatible version.
     */
    if (0xEE == parHdr.id)
    {
        Serial.printf(
            "Found pargen block header in EEPROM: ID:%0X Version:%d.%d Length: %d bytes\n",
            parHdr.id,
            parHdr.major,
            parHdr.minor,
            parHdr.length
        );

        /* TODO: Do version checking here. */
    }
    else
    {
        Serial.println("Fatal: Pargen block header with id 0xEE not present in EEPROM.");
        halt();
    }

    uint16_t delay_ms = eeprom_read_word((const uint16_t*)(&par_UpdateDelay_ms));

    Serial.print( "delay: ");
    Serial.print( delay_ms);
    Serial.println( " ms");
}

/** Print message from parameter block with provided delay parameter.
*/
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