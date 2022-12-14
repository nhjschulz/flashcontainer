import pytest

import datamodel as DM
from  byteconv import ByteConvert

def test_convert_valstr_to_byte():

    assert ByteConvert.json_to_bytes(DM.ParamType.int8, DM.Endianness.LE, "-127") == b'\x81'

    assert ByteConvert.json_to_bytes(DM.ParamType.uint8, DM.Endianness.LE, "0x0") == b'\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint8, DM.Endianness.LE, "0x81") == b'\x81'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint8, DM.Endianness.LE, "0x1") == b'\x01'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint8, DM.Endianness.LE, "0xff") == b'\xff'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint16, DM.Endianness.LE, "0x0000") == b'\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint16, DM.Endianness.LE, "0x1234") == b'\x34\x12'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint32, DM.Endianness.LE, "0x12345678") == b'\x78\x56\x34\x12'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint64, DM.Endianness.LE, "0x12345678abcdef99") == b'\x99\xef\xcd\xab\x78\x56\x34\x12'

    # float result bytes taken from https://www.h-schmidt.net/FloatConverter/IEEE754.html
    assert ByteConvert.json_to_bytes(DM.ParamType.float32, DM.Endianness.LE, "1") ==  b'\x00\x00\x80\x3f'
    assert ByteConvert.json_to_bytes(DM.ParamType.float32, DM.Endianness.LE, "1.0") ==  b'\x00\x00\x80\x3f'
    assert ByteConvert.json_to_bytes(DM.ParamType.float32, DM.Endianness.LE, "-1.0") ==  b'\x00\x00\x80\xbf'
    assert ByteConvert.json_to_bytes(DM.ParamType.float32, DM.Endianness.LE, "3.141592653589793238462643383") == b'\xdb\x0f\x49\x40'

    assert ByteConvert.json_to_bytes(DM.ParamType.float32, DM.Endianness.BE, "1") ==  b'\x3f\x80\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.float32, DM.Endianness.BE, "1.0") ==  b'\x3f\x80\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.float32, DM.Endianness.BE, "-1.0") ==  b'\xbf\x80\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.float32, DM.Endianness.BE, "3.141592653589793238462643383") == b'\x40\x49\x0f\xdb'

    # double result bytes taken from https://www.binaryconvert.com/convert_double.html
    assert ByteConvert.json_to_bytes(DM.ParamType.float64, DM.Endianness.LE, "1") ==  b'\x00\x00\x00\x00\x00\x00\xf0\x3f'
    assert ByteConvert.json_to_bytes(DM.ParamType.float64, DM.Endianness.LE, "1.0") ==  b'\x00\x00\x00\x00\x00\x00\xf0\x3f'
    assert ByteConvert.json_to_bytes(DM.ParamType.float64, DM.Endianness.LE, "-1.0") ==  b'\x00\x00\x00\x00\x00\x00\xf0\xbf'
    assert ByteConvert.json_to_bytes(DM.ParamType.float64, DM.Endianness.LE, "3.141592653589793238462643383") == b'\x18\x2d\x44\x54\xfb\x21\x09\x40'

    assert ByteConvert.json_to_bytes(DM.ParamType.float64, DM.Endianness.BE, "1") ==  b'\x3f\xf0\x00\x00\x00\x00\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.float64, DM.Endianness.BE, "1.0") ==  b'\x3f\xf0\x00\x00\x00\x00\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.float64, DM.Endianness.BE, "-1.0") ==  b'\xbf\xf0\x00\x00\x00\x00\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.float64, DM.Endianness.BE, "3.141592653589793238462643383") == b'\x40\x09\x21\xFB\x54\x44\x2D\x18'

    assert ByteConvert.json_to_bytes(DM.ParamType.uint8, DM.Endianness.BE, "0x0") == b'\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint8, DM.Endianness.BE, "0x81") == b'\x81'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint8, DM.Endianness.BE, "0x1") == b'\x01'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint8, DM.Endianness.BE, "0xff") == b'\xff'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint16, DM.Endianness.BE, "0x0000") == b'\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint16, DM.Endianness.BE, "0x1234") == b'\x12\x34'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint32, DM.Endianness.BE, "0x12345678") == b'\x12\x34\x56\x78'
    assert ByteConvert.json_to_bytes(DM.ParamType.uint64, DM.Endianness.BE, "0x12345678abcdef99") == b'\x12\x34\x56\x78\xab\xcd\xef\x99'

    assert ByteConvert.json_to_bytes(DM.ParamType.int8, DM.Endianness.BE, "-127") == b'\x81'
