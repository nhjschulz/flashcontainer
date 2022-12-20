from flashcontainer import datamodel as DM


def test_parameter_as_gap():

    for length in range(1, 1024):
        gap = DM.Parameter.as_gap(length * 10, length, 0xa5)
        assert gap.comment is None
        assert gap.name is None
        assert gap.type is DM.ParamType.GAPFILL
        assert gap.offset == length * 10
        assert len(gap.value) == length
        assert gap.value == bytearray([0xa5] * length)


def test_header_bytes():
    block = DM.Block(0, None, DM.Endianness.LE, 0x0)
    block.set_header(DM.BlockHeader(0xAFFE, DM.Version(0x1234, 0xabcd, 0x5678), 0xaabbccdd))
    assert block.get_header_bytes() == b'\xfe\xaf\x34\x12\xcd\xab\x78\x56\x00\x00\x00\x00\xdd\xcc\xbb\xaa'

    block.endianess = DM.Endianness.BE
    assert block.get_header_bytes() == b'\xaf\xfe\x12\x34\xab\xcd\x56\x78\x00\x00\x00\x00\xaa\xbb\xcc\xdd'


def test_crc():
    
    # Test input "123456789" with expected CRC 0xCBF43926

    block = DM.Block(0, None, DM.Endianness.LE, 0x0)
    block.set_header(DM.BlockHeader(0, DM.Version(0, 0, 0), 0x100))
    block.add_parameter(DM.Parameter(0x10, "p", DM.ParamType.uint8, b'\x31\x32\x33\x34\x35\x36\x37\x38\x39',None))

    crc_param = DM.Parameter(0x1A, "crc", DM.ParamType.uint32, b'\x00\x00\x00\x00', DM.CrcConfig(start=0x10, end=0x1A))
    block.add_parameter(crc_param)
    block.update_crc()
    assert crc_param.value == b'\x26\x39\xf4\xcb'

    block.endianess = DM.Endianness.BE
    block.update_crc()
    assert crc_param.value == b'\xcb\xf4\x39\x26'

