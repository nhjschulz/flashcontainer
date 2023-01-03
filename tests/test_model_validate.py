import pytest
import pathlib

from flashcontainer import datamodel as DM
from flashcontainer import xmlparser as XP

@pytest.fixture
def example_model():
    """Load example model"""
    sandbox_dir = pathlib.Path(__file__).resolve().parent
    example_xml = pathlib.Path.joinpath(sandbox_dir, "example", "example.xml")

    return XP.XmlParser.from_file(example_xml)

def test_load_example(example_model):
    """Test that example is loadable."""
    assert example_model.validate(None) is True

def test_dublicate_block_name(example_model):
    """Trigger dublicate block name error"""
    name = example_model.container[0].blocks[0].name
    example_model.container[0].blocks[1].name = name
    assert example_model.validate(None) is False

def test_overlapping_block(example_model):
    """Trigger overlapping blocks error"""
    addr = example_model.container[0].blocks[1].addr
    example_model.container[0].blocks[0].addr = addr - 0x99
    assert example_model.validate(None) is False

def test_dublicate_parameter_name(example_model):
    """Trigger dublicate parameter name error"""
    name = example_model.container[0].blocks[0].parameter[0].name
    example_model.container[0].blocks[0].parameter[1].name  = name
    assert example_model.validate(None) is False

def test_overlapping_parameter(example_model):
    """Trigger overlapping parameter error"""
    example_model.container[0].blocks[0].parameter[1].offset -= 1
    assert example_model.validate(None) is False

def test_parameter_exceed_range(example_model):
    """Trigger parameter exceeds block range error"""
    crc_idx = len(example_model.container[0].blocks[0].parameter) - 1
    example_model.container[0].blocks[0].parameter[crc_idx].offset += 1
    assert example_model.validate(None) is False

def test_parameter_outofrange(example_model):
    """Trigger parameter out of block range error"""
    crc_idx = len(example_model.container[0].blocks[0].parameter) - 1
    example_model.container[0].blocks[0].parameter[crc_idx].offset += 4
    assert example_model.validate(None) is False

def test_parameter_header_overlap(example_model):
    """Trigger parameter overlaps header error"""
    example_model.container[0].blocks[0].parameter[0].offset -= 1
    assert example_model.validate(None) is False
