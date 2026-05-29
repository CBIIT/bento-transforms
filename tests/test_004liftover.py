import pytest
from pdb import set_trace

from bento_transforms.converters.liftover import Liftover

testfile = "ccdi-model_3.1.0_cds-model_10.0.0-GC_Release_MAPPING_20250916.tsv"


def test_liftover(samplesd):
    lft = Liftover(samplesd / testfile)
    assert (lft.from_model, lft.from_version) == ("CCDI", "3.1.0")
    assert (lft.to_model, lft.to_version) == ("CDS", "10.0.0-GC_Release")
    assert lft.transforms
    
