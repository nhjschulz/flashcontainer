import pytest
import xmlparser as XP
import datamodel as DM


def test_parameter_as_gap():

    for length in range (1, 1024):
        gap = DM.Parameter.as_gap(length * 10, length, 0xa5)
        assert gap.comment is None
        assert gap.name is None
        assert gap.type is DM.ParamType.GAPFILL
        assert gap.offset == length * 10
        assert len(gap.value) == length
        assert gap.value == bytearray([0xa5] * length)

def test_header_bytes():
    block = DM.Block(0,None, DM.Endianness.LE, 0x0)
    block.set_header(DM.BlockHeader(0xAFFE, DM.Version(0x1234, 0xabcd, 0x5678), 0xaabbccdd))
    assert block.get_header_bytes() == b'\xfe\xaf\x34\x12\xcd\xab\x78\x56\x00\x00\x00\x00\xdd\xcc\xbb\xaa'

    block.endianess = DM.Endianness.BE
    assert block.get_header_bytes() == b'\xaf\xfe\x12\x34\xab\xcd\x56\x78\x00\x00\x00\x00\xaa\xbb\xcc\xdd'