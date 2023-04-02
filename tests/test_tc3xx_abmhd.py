import pytest
import pathlib

import lxml.etree as ET

from flashcontainer import tc3xx
from flashcontainer import tc3xx_abmhd

def test_tc3xx_abmhd_output(tmp_path):
    """Run pargen with enabled writers"""

    sandbox_dir = pathlib.Path(__file__).resolve().parents[1]
    test_collateral = pathlib.Path.joinpath(
        sandbox_dir,
        "tests", 
        "collateral")

    abmhd_data = str(pathlib.Path.joinpath(test_collateral, "abmhd_ref.hex"))
    abmhd_ref = str(pathlib.Path.joinpath(test_collateral, "abmhd_ref.xml"))
    abmhd_new = str(pathlib.Path.joinpath(tmp_path, "abmhd_test.xml"))

    arguments = [ 
        'abmhd', 
        '--stad', '0x81000000',
        '--from', '0x81000000',
        '--to', '0x81000400',
        '--output', abmhd_new,
        '0x81000400',
        abmhd_data,
    ]

    result = tc3xx.tc3xx(arguments)
    assert result == tc3xx_abmhd.RETVAL.OK.value

    parser =  ET.XMLParser(remove_comments=True, remove_blank_text=True)
    ref_xml = ET.parse(abmhd_ref, parser=parser)
    new_xml = ET.parse(abmhd_new, parser=parser)

    ref_str = ET.tostring(ref_xml)
    new_str = ET.tostring(new_xml)

    assert new_str == ref_str
