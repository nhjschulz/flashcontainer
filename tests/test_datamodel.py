from flashcontainer import datamodel as DM


def test_parameter_as_gap():

    for length in range(1, 1024):
        gap = DM.Parameter.as_gap(length * 10, length, 0xa5)
        assert gap.comment is None
        assert gap.name is None
        assert gap.ptype is DM.ParamType.GAPFILL
        assert gap.offset == length * 10
        assert len(gap.value) == length
        assert gap.value == bytearray([0xa5] * length)


def test_header_bytes():
    block = DM.Block(0, None, 0xaabbccdd, DM.Endianness.LE, 0x0)
    block.set_header(DM.BlockHeader(0xAFFE, DM.Version(0x1234, 0xabcd, 0x5678)))
    assert block.get_header_bytes() == b'\xfe\xaf\x34\x12\xcd\xab\x78\x56\x00\x00\x00\x00\xdd\xcc\xbb\xaa'

    block.endianess = DM.Endianness.BE
    assert block.get_header_bytes() == b'\xaf\xfe\x12\x34\xab\xcd\x56\x78\x00\x00\x00\x00\xaa\xbb\xcc\xdd'


def test_block_crc():

    # Test input "123456789" with expected CRC 0xCBF43926

    block = DM.Block(0, None, 0x100, DM.Endianness.LE, 0x0)
    block.set_header(DM.BlockHeader(0, DM.Version(0, 0, 0)))
    block.add_parameter(DM.Parameter(0x10, "p", DM.ParamType.UINT8, b'\x31\x32\x33\x34\x35\x36\x37\x38\x39', None))

    crc_param = DM.Parameter(0x1A, "crc", DM.ParamType.UINT32, b'\x00\x00\x00\x00', DM.CrcData(start=0x10, end=0x18))
    block.add_parameter(crc_param)
    block.update_crcs()
    assert crc_param.value == b'\x26\x39\xf4\xcb'

    block.endianess = DM.Endianness.BE
    block.update_crcs()
    assert crc_param.value == b'\xcb\xf4\x39\x26'


def test_get_bytes_empty():
    block = DM.Block(0, None, 0x0, DM.Endianness.LE, 0xAA)
    assert block.get_bytes() == b''


def test_get_bytes():
    block = DM.Block(0, None, 0x10, DM.Endianness.LE, 0xAA)
    block.set_header(DM.BlockHeader(0, DM.Version(0, 0, 0)))
    assert block.get_bytes() == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00'

    block.add_parameter(DM.Parameter(0x10, "foo", DM.ParamType.UINT8, b'\x55', None))
    assert block.get_bytes() == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x55'

    block.add_parameter(DM.Parameter(0x11, "foo", DM.ParamType.UINT8, b'\xbb', None))
    assert block.get_bytes() == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x55\xbb'


def test_get_bytes_with_gaps():
    block = DM.Block(0, None, 10, DM.Endianness.LE, 0xAA)
    block.fill_gaps()
    assert block.get_bytes() == b'\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa'

    block = DM.Block(0, None, 10, DM.Endianness.LE, 0xAA)
    block.add_parameter(DM.Parameter(0x2, "_2", DM.ParamType.UINT8, b'\x22', None))
    block.add_parameter(DM.Parameter(0x7, "_7", DM.ParamType.UINT8, b'\x77', None))
    block.fill_gaps()
    assert block.get_bytes() == b'\xaa\xaa\x22\xaa\xaa\xaa\xaa\x77\xaa\xaa'

def test_model_str():
    assert DM.Model("hello").__str__() == "Model(hello [])"
    assert DM.Container("hello", 0xabcd).__str__() == "hello @ 0xabcd"
    assert DM.Block(0xFF, "block", 10, DM.Endianness.LE, 0xAA).__str__() == "Block(block @ 0xff)"
    assert DM.CrcData().__str__() == "0x0-0x0  polynomial:0x4C11DB7, 32 Bit, init:0xFFFFFFFF, reverse in:True, reverse out:True, final xor:True, access:1, swap:False"
    assert DM.Version(2,3,5).__str__() == "2.3.5"
    assert DM.Parameter(0x2, "_2", DM.ParamType.UINT8, b'\x22', None).__str__() == "_2 @ 0x2 = 22 len=1(0x1) /* None */"
