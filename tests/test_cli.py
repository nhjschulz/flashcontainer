"""Tests of the command line interfaces of the pargen and tc3xx tools.

The test function test_<name> implements the test case SwTests.tc_<name>.
"""

import pathlib
import sys
from typing import Callable, List

import pytest

from flashcontainer import pargen
from flashcontainer.tc3xx import tc3xx

EXAMPLE_XML = pathlib.Path(__file__).resolve().parent / "example" / "example.xml"


def _run_pargen_cli(monkeypatch: pytest.MonkeyPatch, args: List[str]) -> int:
    """Run the pargen command line interface with the given arguments.

    Args:
        monkeypatch: pytest monkeypatch, used to set sys.argv.
        args: Command line arguments without the program name.

    Returns:
        The pargen exit code.
    """
    monkeypatch.setattr(sys, "argv", ["pargen", *args])
    return pargen.pargen_cli()


def _help_exit_code(tool: Callable[[List[str]], int], args: List[str]) -> int:
    """Call a command line interface which is expected to show the help and exit.

    Args:
        tool: Function calling the command line interface with arguments.
        args: Command line arguments without the program name.

    Returns:
        The exit code of the help output.
    """
    with pytest.raises(SystemExit) as exc_info:
        tool(args)
    return exc_info.value.code


def test_cli_help(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Every tool shows its usage help for '-h' and '--help' and exits with code 0."""

    def run_pargen(args: List[str]) -> int:
        return _run_pargen_cli(monkeypatch, args)

    for option in ("-h", "--help"):
        assert _help_exit_code(run_pargen, [option]) == 0
        out = capsys.readouterr().out
        assert out.startswith("usage: pargen")
        assert "--destdir" in out

        assert _help_exit_code(tc3xx.tc3xx, [option]) == 0
        out = capsys.readouterr().out
        assert out.startswith("usage: tc3xx")
        assert "abmhd" in out

        assert _help_exit_code(tc3xx.tc3xx, ["abmhd", option]) == 0
        assert capsys.readouterr().out.startswith("usage: tc3xx abmhd")


def test_cli_argument_file(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """The options in an '@' argument file are applied, several per line or one per line."""

    out_dir = tmp_path / "out"
    arg_file = tmp_path / "pargen.args"
    arg_file.write_text(
        f"--ihex --gld\n--filename fromfile\n--destdir {out_dir}\n{EXAMPLE_XML}\n", encoding="utf-8")

    assert _run_pargen_cli(monkeypatch, [f"@{arg_file}"]) == pargen.Error.ERROR_OK.value
    assert sorted(path.name for path in out_dir.iterdir()) == ["fromfile.crc", "fromfile.hex", "fromfile.ld"]
