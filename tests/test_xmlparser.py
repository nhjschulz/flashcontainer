import pytest
import xmlparser as XP
import datamodel as DM

def test_parse_int():
    assert XP.XmlParser._parse_int("0") == 0
    assert XP.XmlParser._parse_int("0x0") == 0
    assert XP.XmlParser._parse_int("0xFF") == 255
    assert XP.XmlParser._parse_int("1") == 1
    assert XP.XmlParser._parse_int("-2") == -2
    assert XP.XmlParser._parse_int("0xFFFFFFFF") == 0xFFFFFFFF
    assert XP.XmlParser._parse_int("AFFE") == 0xAFFE

    with pytest.raises(Exception) as e_info:
        XP.XmlParser._parse_int("")

    with pytest.raises(Exception) as e_info:
        XP.XmlParser._parse_int("banana")

    with pytest.raises(Exception) as e_info:
        XP.XmlParser._parse_int("0x1X")

def test_calc_addr():
    assert XP.XmlParser.calc_addr(0x100, 0x0 , "0x0", 1) == 0x100   # numeric offet applied to base
    assert XP.XmlParser.calc_addr(0x100, 0xff , "0x1", 1) == 0x101 # numeric offet applied to base

    # with alignment
    assert XP.XmlParser.calc_addr(0x101, 0xff , "0x1", 2) == 0x102 # numeric offet applied to base
    assert XP.XmlParser.calc_addr(0x101, 0xff , "0x1", 4) == 0x104 # numeric offet applied to base
    assert XP.XmlParser.calc_addr(0x101, 0xff , "0x1", 8) == 0x108 # numeric offet applied to base
    assert XP.XmlParser.calc_addr(0x101, 0xff , "0x1", 16) == 0x110 # numeric offet applied to base
    assert XP.XmlParser.calc_addr(0x102, 0xff , "0x1", 32) == 0x120 # numeric offet applied to base
    assert XP.XmlParser.calc_addr(0x103, 0xff , "0x1", 64) == 0x140 # numeric offet applied to base

    # "."  = run + align
    assert XP.XmlParser.calc_addr(0x10, 0x101 , ".", 1) == 0x101 # offset  added to run
    assert XP.XmlParser.calc_addr(0x10, 0x101 , ".", 2) == 0x102 # offset  added to run
    assert XP.XmlParser.calc_addr(0x10, 0x102 , ".", 2) == 0x102 # offset  added to run

    assert XP.XmlParser.calc_addr(0xEEEE0000, 0xEEEE0000, ".", 1) == 0xEEEE0000  # run = base and "." means current run

def test_convert_valstr_to_byte():

    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.int8, DM.Endianness.LE, "-127") == b'\x81'

    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint8, DM.Endianness.LE, "0x0") == b'\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint8, DM.Endianness.LE, "0x81") == b'\x81'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint8, DM.Endianness.LE, "0x1") == b'\x01'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint8, DM.Endianness.LE, "0xff") == b'\xff'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint16, DM.Endianness.LE, "0x0000") == b'\x00\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint16, DM.Endianness.LE, "0x1234") == b'\x34\x12'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint32, DM.Endianness.LE, "0x12345678") == b'\x78\x56\x34\x12'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint64, DM.Endianness.LE, "0x12345678abcdef99") == b'\x99\xef\xcd\xab\x78\x56\x34\x12'

    # float result bytes taken from https://www.h-schmidt.net/FloatConverter/IEEE754.html
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float32, DM.Endianness.LE, "1") ==  b'\x00\x00\x80\x3f'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float32, DM.Endianness.LE, "1.0") ==  b'\x00\x00\x80\x3f'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float32, DM.Endianness.LE, "-1.0") ==  b'\x00\x00\x80\xbf'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float32, DM.Endianness.LE, "3.141592653589793238462643383") == b'\xdb\x0f\x49\x40'

    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float32, DM.Endianness.BE, "1") ==  b'\x3f\x80\x00\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float32, DM.Endianness.BE, "1.0") ==  b'\x3f\x80\x00\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float32, DM.Endianness.BE, "-1.0") ==  b'\xbf\x80\x00\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float32, DM.Endianness.BE, "3.141592653589793238462643383") == b'\x40\x49\x0f\xdb'

    # double result bytes taken from https://www.binaryconvert.com/convert_double.html
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float64, DM.Endianness.LE, "1") ==  b'\x00\x00\x00\x00\x00\x00\xf0\x3f'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float64, DM.Endianness.LE, "1.0") ==  b'\x00\x00\x00\x00\x00\x00\xf0\x3f'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float64, DM.Endianness.LE, "-1.0") ==  b'\x00\x00\x00\x00\x00\x00\xf0\xbf'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float64, DM.Endianness.LE, "3.141592653589793238462643383") == b'\x18\x2d\x44\x54\xfb\x21\x09\x40'

    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float64, DM.Endianness.BE, "1") ==  b'\x3f\xf0\x00\x00\x00\x00\x00\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float64, DM.Endianness.BE, "1.0") ==  b'\x3f\xf0\x00\x00\x00\x00\x00\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float64, DM.Endianness.BE, "-1.0") ==  b'\xbf\xf0\x00\x00\x00\x00\x00\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.float64, DM.Endianness.BE, "3.141592653589793238462643383") == b'\x40\x09\x21\xFB\x54\x44\x2D\x18'

    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint8, DM.Endianness.BE, "0x0") == b'\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint8, DM.Endianness.BE, "0x81") == b'\x81'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint8, DM.Endianness.BE, "0x1") == b'\x01'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint8, DM.Endianness.BE, "0xff") == b'\xff'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint16, DM.Endianness.BE, "0x0000") == b'\x00\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint16, DM.Endianness.BE, "0x1234") == b'\x12\x34'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint32, DM.Endianness.BE, "0x12345678") == b'\x12\x34\x56\x78'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.uint64, DM.Endianness.BE, "0x12345678abcdef99") == b'\x12\x34\x56\x78\xab\xcd\xef\x99'

    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.int8, DM.Endianness.BE, "-127") == b'\x81'

    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.utf8, DM.Endianness.LE, "\"\"") == b'\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.utf8, DM.Endianness.BE, "\"\"") == b'\x00'
    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.utf8, DM.Endianness.BE, "\"hello world!\"") == b'hello world!\x00'

    assert XP.XmlParser._convert_valstr_to_bytes(DM.ParamType.utf8, DM.Endianness.BE, "\"诺伯特\"") == b'\xe8\xaf\xba\xe4\xbc\xaf\xe7\x89\xb9\x00'
