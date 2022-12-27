from flashcontainer import datamodel as DM
from flashcontainer.byteconv import ByteConvert


def test_convert_valstr_to_byte():

    assert ByteConvert.json_to_bytes(DM.ParamType.INT8, DM.Endianness.LE, "-127") == b'\x81'

    assert ByteConvert.json_to_bytes(DM.ParamType.UINT8, DM.Endianness.LE, "0x0") == b'\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT8, DM.Endianness.LE, "0x81") == b'\x81'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT8, DM.Endianness.LE, "0x1") == b'\x01'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT8, DM.Endianness.LE, "0xff") == b'\xff'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT16, DM.Endianness.LE, "0x0000") == b'\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT16, DM.Endianness.LE, "0x1234") == b'\x34\x12'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT32, DM.Endianness.LE, "0x12345678") == b'\x78\x56\x34\x12'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT64, DM.Endianness.LE, "0x12345678abcdef99") == b'\x99\xef\xcd\xab\x78\x56\x34\x12'

    # float result bytes taken from https://www.h-schmidt.net/FloatConverter/IEEE754.html
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT32, DM.Endianness.LE, "1") ==  b'\x00\x00\x80\x3f'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT32, DM.Endianness.LE, "1.0") ==  b'\x00\x00\x80\x3f'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT32, DM.Endianness.LE, "-1.0") ==  b'\x00\x00\x80\xbf'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT32, DM.Endianness.LE, "3.141592653589793238462643383") == b'\xdb\x0f\x49\x40'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT32, DM.Endianness.LE, "1.0E+2") == b'\x00\x00\xc8\x42'

    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT32, DM.Endianness.BE, "1") ==  b'\x3f\x80\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT32, DM.Endianness.BE, "1.0") ==  b'\x3f\x80\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT32, DM.Endianness.BE, "-1.0") ==  b'\xbf\x80\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT32, DM.Endianness.BE, "3.141592653589793238462643383") == b'\x40\x49\x0f\xdb'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT32, DM.Endianness.BE, "1.0E+2") == b'\x42\xc8\x00\x00'

    # double result bytes taken from https://www.binaryconvert.com/convert_double.html
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT64, DM.Endianness.LE, "1") ==  b'\x00\x00\x00\x00\x00\x00\xf0\x3f'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT64, DM.Endianness.LE, "1.0") ==  b'\x00\x00\x00\x00\x00\x00\xf0\x3f'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT64, DM.Endianness.LE, "-1.0") ==  b'\x00\x00\x00\x00\x00\x00\xf0\xbf'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT64, DM.Endianness.LE, "3.141592653589793238462643383") == b'\x18\x2d\x44\x54\xfb\x21\x09\x40'

    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT64, DM.Endianness.BE, "1") ==  b'\x3f\xf0\x00\x00\x00\x00\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT64, DM.Endianness.BE, "1.0") ==  b'\x3f\xf0\x00\x00\x00\x00\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT64, DM.Endianness.BE, "-1.0") ==  b'\xbf\xf0\x00\x00\x00\x00\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.FLOAT64, DM.Endianness.BE, "3.141592653589793238462643383") == b'\x40\x09\x21\xFB\x54\x44\x2D\x18'

    assert ByteConvert.json_to_bytes(DM.ParamType.UINT8, DM.Endianness.BE, "0x0") == b'\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT8, DM.Endianness.BE, "0x81") == b'\x81'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT8, DM.Endianness.BE, "0x1") == b'\x01'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT8, DM.Endianness.BE, "0xff") == b'\xff'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT16, DM.Endianness.BE, "0x0000") == b'\x00\x00'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT16, DM.Endianness.BE, "0x1234") == b'\x12\x34'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT32, DM.Endianness.BE, "0x12345678") == b'\x12\x34\x56\x78'
    assert ByteConvert.json_to_bytes(DM.ParamType.UINT64, DM.Endianness.BE, "0x12345678abcdef99") == b'\x12\x34\x56\x78\xab\xcd\xef\x99'

    assert ByteConvert.json_to_bytes(DM.ParamType.INT8, DM.Endianness.BE, "-127") == b'\x81'


def _trim(text: str) -> str:
    "remove newlines, tabls and multiple spaces from formatted string for easier compare"
    result = text.replace('\r', '')
    result = result.replace('\n', '')
    result = result.replace('\t', '')
    result = result.replace(' ', '')

    return result


def test_bytes_to_c_init():
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT8, DM.Endianness.LE, b'\x00')) == "0"
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT8, DM.Endianness.LE, b'\x00\x01')) == '{0,1}'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT16, DM.Endianness.LE, b'\xff\x11')) == '4607'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT16, DM.Endianness.LE, b'\xaa\xbb\xcc\xdd')) == '{-17494,-8756}'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT32, DM.Endianness.LE, b'\x00\x00\x00\x00')) == '0'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT32, DM.Endianness.LE, b'\xb2\x9e\x43\xff')) == '-12345678'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT32, DM.Endianness.LE, b'\xb2\x9e\x43\xff\xb1\x9e\x43\xff')) == '{-12345678,-12345679}'

    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT8, DM.Endianness.BE, b'\x00')) == "0"
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT8, DM.Endianness.BE, b'\x00\x01')) == '{0,1}'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT16, DM.Endianness.BE, b'\xff\x11')) == '-239'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT16, DM.Endianness.BE, b'\xaa\xbb\xcc\xdd')) == '{-21829,-13091}'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT32, DM.Endianness.BE, b'\x00\x00\x00\x00')) == '0'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT32, DM.Endianness.BE, b'\xb2\x9e\x43\xff')) == '-1298250753'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.INT32, DM.Endianness.BE, b'\xb2\x9e\x43\xff\xb1\x9e\x43\xff')) == '{-1298250753,-1315027969}'

    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.FLOAT32, DM.Endianness.BE, b'\x3f\xc0\x00\x00')) == '1.50000000'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.FLOAT32, DM.Endianness.BE, b'\x3f\xc0\x00\x00\x3f\xc0\x00\x00')) == '{1.50000000,1.50000000}'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.FLOAT32, DM.Endianness.LE, b'\x00\x00\xc0\x3f')) == '1.50000000'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.FLOAT32, DM.Endianness.LE, b'\x00\x00\xc0\x3f\x00\x00\xc0\x3f')) == '{1.50000000,1.50000000}'

    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.FLOAT64, DM.Endianness.BE, b'\x40\x30\x0C\x01\xA3\x6E\x2E\xB2')) == '16.04690000'
    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.FLOAT64, DM.Endianness.LE, b'\xB2\x2e\x6e\xa3\x01\x0c\x30\x40')) == '16.04690000'

    assert _trim(ByteConvert.bytes_to_c_init(DM.ParamType.UTF8, DM.Endianness.LE, b'\x30\x31\x32\x33\x00')) == '{0x30,0x31,0x32,0x33,0x00}'
