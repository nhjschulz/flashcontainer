import pytest
from flashcontainer import xmlparser as XP


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
    assert XP.XmlParser.calc_addr(0x100, 0x0, "0x0", 1) == 0x100   # numeric offset applied to base
    assert XP.XmlParser.calc_addr(0x100, 0xff, "0x1", 1) == 0x101  # numeric offset applied to base

    # with alignment
    assert XP.XmlParser.calc_addr(0x101, 0xff, "0x1", 2) == 0x102  # numeric offset applied to base
    assert XP.XmlParser.calc_addr(0x101, 0xff, "0x1", 4) == 0x104  # numeric offset applied to base
    assert XP.XmlParser.calc_addr(0x101, 0xff, "0x1", 8) == 0x108  # numeric offset applied to base
    assert XP.XmlParser.calc_addr(0x101, 0xff, "0x1", 16) == 0x110  # numeric offset applied to base
    assert XP.XmlParser.calc_addr(0x102, 0xff, "0x1", 32) == 0x120  # numeric offset applied to base
    assert XP.XmlParser.calc_addr(0x103, 0xff, "0x1", 64) == 0x140  # numeric offset applied to base

    # "."  = run + align
    assert XP.XmlParser.calc_addr(0x10, 0x101, ".", 1) == 0x101  # offset  added to run
    assert XP.XmlParser.calc_addr(0x10, 0x101, ".", 2) == 0x102  # offset  added to run
    assert XP.XmlParser.calc_addr(0x10, 0x102, ".", 2) == 0x102  # offset  added to run

    assert XP.XmlParser.calc_addr(0xEEEE0000, 0xEEEE0000, ".", 1) == 0xEEEE0000  # run = base and "." means current run
