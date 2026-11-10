"""Tests of the pargen tool: result codes and generated outputs.

The test function test_<name> implements the test case SwTests.tc_<name>.
"""

import json
import pathlib
import re
import sys
from typing import Dict, List, Type

import pytest

from flashcontainer import pargen
from flashcontainer.model import datamodel as DM
from flashcontainer.model.xmlparser import XmlParser
from flashcontainer.writer.a2lwriter import A2lWriter
from flashcontainer.writer.gnuldwriter import GnuLdWriter
from flashcontainer.writer.pyhexdumpwriter import PyHexDumpWriter

def test_pargen_errors(tmp_path):
    """Run pargen with options to return errors"""

    sandbox_dir = pathlib.Path(__file__).resolve().parent
    example_xml = pathlib.Path.joinpath(sandbox_dir, "example", "example.xml")

    # run without writer should succeed
    result = pargen.pargen(
        cfgfile=example_xml,
        filename=None,
        outdir=tmp_path,
        static=False,
        writers=[])
    assert result == pargen.Error.ERROR_OK.value

    # invalid model

    result = pargen.pargen(
        cfgfile=pathlib.Path.joinpath(sandbox_dir, "collateral", "invalid.xml"),
        filename=None,
        outdir=tmp_path,
        static=False,
        writers=[])
    assert result == pargen.Error.ERROR_INVALID_FORMAT.value

    # invalid filename

    result = pargen.pargen(
        cfgfile=pathlib.Path.joinpath(sandbox_dir, "collateral", "invalidX.xml"),
        filename=None,
        outdir=tmp_path,
        static=False,
        writers=[])
    assert result == pargen.Error.ERROR_FILE_NOT_FOUND.value

    # fail validation

    result = pargen.pargen(
        cfgfile=pathlib.Path.joinpath(sandbox_dir, "collateral", "fail_validation.xml"),
        filename=None,
        outdir=tmp_path,
        static=False,
        writers=[])
    assert result == pargen.Error.ERROR_VALIDATION_FAIL.value

def test_pargen_output(tmp_path):
    """Run pargen with enabled writers"""
    sandbox_dir = pathlib.Path(__file__).resolve().parents[1]
    arduino_example = pathlib.Path.joinpath(sandbox_dir, "examples", "arduino")

    writer_list = []
    for writer in pargen._WRITER:  # pylint: disable=protected-access
        writer_list.append(writer["class"])

    result = pargen.pargen(
        cfgfile=pathlib.Path.joinpath(arduino_example, "param", "param.xml"),
        filename="pytest",
        outdir=tmp_path,
        static=False,
        writers=writer_list)
    assert result == pargen.Error.ERROR_OK.value

    # diff content (lines with ":")
    gen_lines = []
    with open(pathlib.Path.joinpath(tmp_path, "pytest.hex"), encoding="utf-8") as file:
        for line in file:
            if line[0] == ":":
                gen_lines.append(line)

    reference_lines = []
    with open(pathlib.Path.joinpath(arduino_example, "param", "param.hex"), encoding="utf-8") as file:
        for line in file:
            if line[0] == ":":
                reference_lines.append(line)

    entries = len(gen_lines)
    assert entries == len(reference_lines)

    for idx in range(0,entries):
        assert gen_lines[idx] == reference_lines[idx]

    crc = 0x0
    with open(pathlib.Path.joinpath(tmp_path, "pytest.crc"), encoding="utf-8") as file:
        crc = int(file.readline(), 16)
        print(crc)

    assert crc == 0x2144DF1C


# Output generation tests: the outputs of tests/example/example.xml are checked against
# its parsed data model.

EXAMPLE_XML = pathlib.Path(__file__).resolve().parent / "example" / "example.xml"

# Expected A2L data type and limits per parameter type.
A2L_TYPES = {
    DM.ParamType.UINT8: ("UBYTE", 0, 255),
    DM.ParamType.UINT16: ("UWORD", 0, 65535),
    DM.ParamType.UINT32: ("ULONG", 0, 4294967295),
    DM.ParamType.INT16: ("SWORD", -32768, 32767),
    DM.ParamType.FLOAT32: ("FLOAT32_IEEE", -3.402823466e+38, 3.402823466e+38),
    DM.ParamType.UTF8: ("UBYTE", 0, 255),
}

# Element size in bytes and pyHexDump data type (little endian) per parameter type.
PARAM_TYPES = {
    DM.ParamType.UINT8: (1, "uint8"),
    DM.ParamType.UINT16: (2, "uint16le"),
    DM.ParamType.UINT32: (4, "uint32le"),
    DM.ParamType.INT16: (2, "int16le"),
    DM.ParamType.FLOAT32: (4, "float32le"),
    DM.ParamType.UTF8: (1, "utf8"),
}


def _example_blocks() -> List[DM.Block]:
    """Parse the example definition.

    Returns:
        The blocks of the example, with their header and parameters.
    """
    model = XmlParser.from_file(str(EXAMPLE_XML))
    assert model is not None
    return [block for container in model.container for block in container.blocks]


def _parameters(block: DM.Block) -> List[DM.Parameter]:
    """Get the parameters of a block without gap fills.

    Args:
        block: The block.

    Returns:
        The parameters in address order.
    """
    return [param for param in block.parameter if param.ptype != DM.ParamType.GAPFILL]


def _generate(out_dir: pathlib.Path, writers: List[Type[DM.Walker]], static: bool = True) -> Dict[str, bytes]:
    """Generate the outputs of the example definition.

    Args:
        out_dir: Output directory.
        writers: Writer classes to run.
        static: Generate static output without date and build key.

    Returns:
        The content of each generated file by file name.
    """
    result = pargen.pargen(cfgfile=str(EXAMPLE_XML), filename="example", outdir=out_dir, static=static,
                           writers=writers)
    assert result == pargen.Error.ERROR_OK.value
    return {path.name: path.read_bytes() for path in sorted(out_dir.iterdir())}


def test_output_selection(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """Exactly the selected outputs are generated, into the selected directory with the selected base name."""

    selections = [
        (["--gld", "--a2l"], ["sel.a2l", "sel.ld"]),
        (["--csrc"], ["sel.c", "sel.h"]),
        (["--ihex", "--pyhexdump"], ["sel.crc", "sel.hex", "sel.pyhexdump"]),
    ]
    for index, (options, expected) in enumerate(selections):
        out_dir = tmp_path / f"out{index}"
        monkeypatch.setattr(sys, "argv", ["pargen", *options, "--destdir", str(out_dir),
                                          "--filename", "sel", str(EXAMPLE_XML)])
        assert pargen.pargen_cli() == pargen.Error.ERROR_OK.value
        assert sorted(path.name for path in out_dir.iterdir()) == expected

    # Without --filename, the base name is the name of the definition file.
    out_dir = tmp_path / "default_name"
    monkeypatch.setattr(sys, "argv", ["pargen", "--gld", "--destdir", str(out_dir), str(EXAMPLE_XML)])
    assert pargen.pargen_cli() == pargen.Error.ERROR_OK.value
    assert [path.name for path in out_dir.iterdir()] == ["example.ld"]


def test_output_gld(tmp_path: pathlib.Path) -> None:
    """The linker include file assigns every block header and parameter symbol its absolute address."""

    content = _generate(tmp_path, [GnuLdWriter])["example.ld"].decode("utf-8")
    symbols = [(name, int(addr, 16))
               for name, addr in re.findall(r"^(\w+)\s+= (0x[0-9a-fA-F]+);", content, re.MULTILINE)]

    expected = []
    for block in _example_blocks():
        expected.append((f"{block.name}_blkhdr", block.addr))
        expected.extend((param.name, param.offset) for param in _parameters(block))
    assert symbols == expected


def test_output_a2l(tmp_path: pathlib.Path) -> None:
    """The A2L file describes every parameter with data type, limits, array size and address."""

    content = _generate(tmp_path, [A2lWriter])["example.a2l"].decode("utf-8")
    measurements = []
    for body in re.findall(r"/begin MEASUREMENT (.*?)/end MEASUREMENT", content, re.DOTALL):
        lines = [line.strip() for line in body.strip().splitlines() if line.strip()]
        keywords = dict(line.split(" ", 1) for line in lines[8:] if " " in line)
        measurements.append((lines[0], lines[2], float(lines[6]), float(lines[7]),
                             int(keywords.get("MATRIX_DIM", "1")), int(keywords["ECU_ADDRESS"], 16)))

    expected = []
    for block in _example_blocks():
        for param in _parameters(block):
            a2l_type, lower, upper = A2L_TYPES[param.ptype]
            count = len(param.value) // PARAM_TYPES[param.ptype][0]
            expected.append((param.name, a2l_type, lower, upper, count, param.offset))
    assert measurements == expected

    # A negative float value is within the limits of its parameter.
    negative_pi = next(m for m in measurements if m[0] == "negativePi")
    assert negative_pi[2] < -3.14 < negative_pi[3]

    # The block headers are described as structure instances at the block address.
    instances = re.findall(r"/begin INSTANCE\s+(\w+)\s+\".*?\"\s+(\w+)\s+(0x[0-9a-fA-F]+)", content)
    assert [(name, int(addr, 16)) for name, _, addr in instances] == \
        [(f"{block.name}_blkhdr", block.addr) for block in _example_blocks()]


def test_output_pyhexdump(tmp_path: pathlib.Path) -> None:
    """The pyHexDump configuration lists every block header and parameter with address, data type and count."""

    config = json.loads(_generate(tmp_path, [PyHexDumpWriter])["example.pyhexdump"])
    elements = [(element["name"], int(element["addr"], 16), element["dataType"], element["count"])
                for element in config["elements"]]

    expected = []
    for block in _example_blocks():
        expected.append((f"{block.name}_blkhdr", block.addr, "pargen_header_le_t", 1))
        for param in _parameters(block):
            size, data_type = PARAM_TYPES[param.ptype]
            expected.append((param.name, param.offset, data_type, len(param.value) // size))
    assert elements == expected

    # The data type of the block headers is defined as structure.
    assert "pargen_header_le_t" in [structure["name"] for structure in config["structures"]]


def test_output_static(tmp_path: pathlib.Path) -> None:
    """With static output, generating twice gives identical files. Without, date and build key differ."""

    writers = [writer["class"] for writer in pargen._WRITER]  # pylint: disable=protected-access

    first = _generate(tmp_path / "static", writers)
    second = _generate(tmp_path / "static", writers)
    assert sorted(first) == ["example.a2l", "example.c", "example.crc", "example.h", "example.hex",
                             "example.ld", "example.pyhexdump"]
    assert first == second

    first = _generate(tmp_path / "dynamic", writers, static=False)
    second = _generate(tmp_path / "dynamic", writers, static=False)
    assert first["example.hex"] == second["example.hex"]
    assert first["example.ld"] != second["example.ld"]
