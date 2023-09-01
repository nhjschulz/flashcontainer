import pytest
import pathlib

from flashcontainer import xmlparser as XP
from flashcontainer import datamodel

def test_parse_int():
    parser = XP.XmlParser()
    assert parser._parse_int("0") == 0
    assert parser._parse_int("0x0") == 0
    assert parser._parse_int("0xFF") == 255
    assert parser._parse_int("1") == 1
    assert parser._parse_int("-2") == -2
    assert parser._parse_int("0xFFFFFFFF") == 0xFFFFFFFF
    assert parser._parse_int("AFFE") == 0xAFFE

    with pytest.raises(Exception) as e_info:
        parser._parse_int("")

    with pytest.raises(Exception) as e_info:
        parser._parse_int("banana")

    with pytest.raises(Exception) as e_info:
        parser._parse_int("0x1X")


def test_calc_addr():
    parser = XP.XmlParser()
    assert parser.calc_addr(0x100, 0x0, "0x0", 1) == 0x100   # numeric offset applied to base
    assert parser.calc_addr(0x100, 0xff, "0x1", 1) == 0x101  # numeric offset applied to base

    # with alignment
    assert parser.calc_addr(0x101, 0xff, "0x1", 2) == 0x102  # numeric offset applied to base
    assert parser.calc_addr(0x101, 0xff, "0x1", 4) == 0x104  # numeric offset applied to base
    assert parser.calc_addr(0x101, 0xff, "0x1", 8) == 0x108  # numeric offset applied to base
    assert parser.calc_addr(0x101, 0xff, "0x1", 16) == 0x110  # numeric offset applied to base
    assert parser.calc_addr(0x102, 0xff, "0x1", 32) == 0x120  # numeric offset applied to base
    assert parser.calc_addr(0x103, 0xff, "0x1", 64) == 0x140  # numeric offset applied to base

    # "."  = run + align
    assert parser.calc_addr(0x10, 0x101, ".", 1) == 0x101  # offset  added to run
    assert parser.calc_addr(0x10, 0x101, ".", 2) == 0x102  # offset  added to run
    assert parser.calc_addr(0x10, 0x102, ".", 2) == 0x102  # offset  added to run

    assert parser.calc_addr(0xEEEE0000, 0xEEEE0000, ".", 1) == 0xEEEE0000  # run = base and "." means current run

def test_parse_invalid_xml():
    sandbox_dir = pathlib.Path(__file__).resolve().parent
    invalid_xml = pathlib.Path.joinpath(sandbox_dir, "collateral", "invalid.xml")

    assert XP.XmlParser.from_file(invalid_xml) == None

def test_parse_safety_example():
    sandbox_dir = pathlib.Path(__file__).resolve().parents[1]
    safety_xml = pathlib.Path.joinpath(sandbox_dir, "examples", "safety", "safety.xml")
    model = XP.XmlParser.from_file(safety_xml)
    assert model.validate(None) is True

    assert model is not None
    assert model.container is not None
    assert len(model.container) == 1
    assert model.container[0].name == "CodeFlash"
    assert model.container[0].addr == 0x80000000
    assert model.container[0].blocks is not None
    assert len(model.container[0].blocks) == 1
    assert model.container[0].blocks[0].name == "paraBlkSafety"
    assert model.container[0].blocks[0].addr == 0x80000000
    assert model.container[0].blocks[0].length == 0x200
    assert model.container[0].blocks[0].endianess == datamodel.Endianness.LE
    assert model.container[0].blocks[0].fill == 0xAA
    assert model.container[0].blocks[0].comment == "This block is used for safety related parameters using header identification and block crc."
    assert model.container[0].blocks[0].header is not None
    assert model.container[0].blocks[0].header.block_id == 0xFF01
    assert model.container[0].blocks[0].header.version.major == 1
    assert model.container[0].blocks[0].header.version.minor == 0
    assert model.container[0].blocks[0].header.version.version == 3

    params = model.container[0].blocks[0].parameter
    assert params is not None
    assert len(params) == 3
    assert params[0].name == "calibration"
    assert params[0].offset == 0x80000010
    assert params[0].ptype == datamodel.ParamType.FLOAT32
    assert params[0].comment == "Safety critical calibration values."
    assert params[0].value == b'\x00\x00\x80?ff\x06\xc0\xcd\xccL@\x00\x00\x90@\xcd\xcc\xac@\x00\x00\xd0@'
    assert params[0].crc_cfg is None

    assert params[1].name is None
    assert params[1].offset == 0x80000028
    assert params[1].ptype == datamodel.ParamType.GAPFILL
    assert params[1].comment is None
    assert params[1].crc_cfg is None

    assert params[2].name == "crc"
    assert params[2].offset == 0x800001FC
    assert params[2].ptype == datamodel.ParamType.UINT32
    assert params[2].comment == "Entire block crc32 (IEEE802.3)"
    assert params[2].crc_cfg is not None
    assert params[2].crc_cfg == datamodel.CrcData(start=0x80000000, end=0x800001FB)

def test_modify_value():
    sandbox_dir = pathlib.Path(__file__).resolve().parents[1]
    safety_xml = pathlib.Path.joinpath(sandbox_dir, "examples", "safety", "safety.xml")
    model = XP.XmlParser.from_file(safety_xml, {"calibration":"[0,1,3,4,5,6,7,8,9,10]", "idontexist": 3})
    assert model.validate(None) is True
    print(model.container[0].blocks[0].parameter[0].value)
    assert model.container[0].blocks[0].parameter[0].value == b'\x00\x00\x00\x00\x00\x00\x80?\x00\x00@@\x00\x00\x80@\x00\x00\xa0@\x00\x00\xc0@\x00\x00\xe0@\x00\x00\x00A\x00\x00\x10A\x00\x00 A'

def test_parse_structs():
    """ Test for the correct parsing of xml defined structs """
    sandbox_dir = pathlib.Path(__file__).resolve().parent
    test_xml = pathlib.Path.joinpath(sandbox_dir, "example", "structexample.xml")
    model = XP.XmlParser.from_file(test_xml)
    assert model.validate(None) is True

    # check parsing of struct tags
    assert len(model.datastructs) == 2
    assert len(model.datastructs[0].fields) == 3
    assert "super simple" in model.datastructs[0].comment
    assert len(model.datastructs[1].fields) == 5
    assert "space" in model.get_struct_by_name("ComplexS").fields[2].comment
    assert model.get_struct_by_name("idonotexist") is None

    # check parsing of complex parameters
    assert model.container[0].blocks[2].addr == 0x80000400
    params = model.container[0].blocks[2].parameter
    assert params[0].name == "simpy"
    assert params[0].offset == model.container[0].blocks[2].addr + 0x10
    assert params[0].value == b'\x03\x05\xd7'

    assert params[1].name == "biggy"
    assert params[1].offset == params[0].offset + 3
    assert params[1].value == b'\x01\xFF\xFF\xFF\xFF\x7F\x96\x98\x00\x00\x00\x00\x00' + \
                                b'\xFF\xFF\x01\x00\x04\x00\x10\x00\x40\x00'

def test_parse_invalid_structs():
    """Test invalid struct definitions or parameter values"""
    sandbox_dir = pathlib.Path(__file__).resolve().parent
    garbage_dir = pathlib.Path.joinpath(sandbox_dir, "collateral", "garbage")
    for invalid_xml in garbage_dir.iterdir():
        assert XP.XmlParser.from_file(invalid_xml) is None
