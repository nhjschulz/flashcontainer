from flashcontainer.checksum import Crc, CrcConfig


def test_swap():
    crc1 = Crc(CrcConfig(access=8, swap=True))
    crc2 = Crc(CrcConfig(access=16, swap=True))
    crc4 = Crc(CrcConfig(access=32, swap=True))
    crc8 = Crc(CrcConfig(access=64, swap=True))

    assert crc1.prepare(b'\xaa\xbb\xcc\xdd') == b'\xaa\xbb\xcc\xdd'
    assert crc2.prepare(b'\xaa\xbb\xcc\xdd') == b'\xbb\xaa\xdd\xcc'
    assert crc4.prepare(b'\xaa\xbb\xcc\xdd') == b'\xdd\xcc\xbb\xaa'
    assert crc8.prepare(b'\x12\x34\x56\x78\x87\x65\x43\x21') == b'\x21\x43\x65\x87\x78\x56\x34\x12'

    crc1 = Crc(CrcConfig(access=8, swap=False))
    crc2 = Crc(CrcConfig(access=16, swap=False))
    crc4 = Crc(CrcConfig(access=32, swap=False))
    crc8 = Crc(CrcConfig(access=64, swap=False))

    assert crc1.prepare(b'\xaa\xbb\xcc\xdd') == b'\xaa\xbb\xcc\xdd'
    assert crc2.prepare(b'\xaa\xbb\xcc\xdd') == b'\xaa\xbb\xcc\xdd'
    assert crc4.prepare(b'\xaa\xbb\xcc\xdd') == b'\xaa\xbb\xcc\xdd'
    assert crc8.prepare(b'\x12\x34\x56\x78\x87\x65\x43\x21') == b'\x12\x34\x56\x78\x87\x65\x43\x21'
