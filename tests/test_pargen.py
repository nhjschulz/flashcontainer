import pytest
import pathlib

from flashcontainer import pargen

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
    for writer in pargen._WRITER:
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
